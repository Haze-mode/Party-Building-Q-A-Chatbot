# -*- coding: utf-8 -*-
import os  # 导入操作系统相关功能模块
import jieba  # 导入中文分词库
import dataclasses as dc  # 导入数据类模块并重命名为dc
import functools  # 导入函数工具模块
from collections.abc import Callable, Mapping, Sequence  # 导入抽象基类
from pathlib import Path  # 导入路径处理模块
from typing import Annotated, Any, Union  # 导入类型注解相关模块
import numpy as np  # 导入数值计算库并重命名为np
import ruamel.yaml as yaml  # 导入YAML处理库并重命名为yaml
import torch  # 导入PyTorch深度学习库
import typer  # 导入命令行参数解析库
from datasets import Dataset, Split  # 导入数据集相关类
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction  # 导入BLEU评分相关函数
from peft import PeftConfig, get_peft_config, get_peft_model  # 导入参数高效微调相关函数
from rouge_chinese import Rouge  # 导入中文Rouge评估工具
from torch import nn  # 导入神经网络模块
from transformers import (  # 导入Transformers库中的相关类和函数
    AutoModelForCausalLM,
    AutoTokenizer,
    EvalPrediction,
    GenerationConfig,
    PreTrainedTokenizer,
    Seq2SeqTrainingArguments,
)
from transformers import DataCollatorForSeq2Seq as _DataCollatorForSeq2Seq  # 导入并重命名数据整理器
from transformers import Seq2SeqTrainer as _Seq2SeqTrainer  # 导入并重命名训练器
from datasets import load_dataset, DatasetDict, NamedSplit  # 导入数据集加载和处理相关类
from typing import Optional  # 导入可选类型注解

app = typer.Typer(pretty_exceptions_show_locals=False)  # 创建Typer应用对象，禁用异常中显示局部变量


class DataCollatorForSeq2Seq(_DataCollatorForSeq2Seq):  # 定义自定义的数据整理器类，继承自transformers库的数据整理器
    def __call__(self, features, return_tensors=None):  # 重写调用方法，处理输入特征
        output_ids = ([feature['output_ids'] for feature in features] if 'output_ids' in features[0].keys() else None)  # 提取输出ID，如果存在的话
        if output_ids is not None:  # 如果存在输出ID
            max_output_length = max(len(out) for out in output_ids)  # 计算最大输出长度
            if self.pad_to_multiple_of is not None:  # 如果需要填充到特定倍数
                max_output_length = (
                        (
                                max_output_length + self.pad_to_multiple_of - 1) //
                        self.pad_to_multiple_of * self.pad_to_multiple_of
                )  # 调整最大输出长度为指定倍数
            for feature in features:  # 遍历每个特征
                remainder = [self.tokenizer.pad_token_id] * (
                        max_output_length - len(feature['output_ids'])
                )  # 创建填充token序列
                if isinstance(feature['output_ids'], list):  # 如果输出ID是列表类型
                    feature['output_ids'] = feature['output_ids'] + remainder  # 直接添加填充token
                else:  # 否则（可能是numpy数组）
                    feature['output_ids'] = np.concatenate(
                        [feature['output_ids'], remainder]
                    ).astype(np.int64)  # 连接数组并转换类型
        return super().__call__(features, return_tensors)  # 调用父类方法处理其他特征


class Seq2SeqTrainer(_Seq2SeqTrainer):  # 定义自定义的序列到序列训练器，继承自transformers库的训练器
    # Not Support for apex  # 注释：不支持apex加速库
    def training_step(self, model: nn.Module, inputs: dict[str, Any]) -> torch.Tensor:  # 重写训练步骤方法

        model.train()  # 设置模型为训练模式
        inputs = self._prepare_inputs(inputs)  # 准备输入数据

        with self.compute_loss_context_manager():  # 使用损失计算上下文管理器
            loss = self.compute_loss(model, inputs)  # 计算损失

        if self.args.n_gpu > 1:  # 如果使用多个GPU
            loss = loss.mean()  # 对多GPU的损失取平均
        self.accelerator.backward(loss)  # 反向传播计算梯度
        detached_loss = loss.detach() / self.args.gradient_accumulation_steps  # 分离损失张量并根据梯度累积步数调整
        del inputs  # 删除输入数据释放内存
        torch.cuda.empty_cache()  # 清空CUDA缓存
        return detached_loss  # 返回分离后的损失

    def prediction_step(
            self,
            model: nn.Module,
            inputs: dict[str, Any],
            prediction_loss_only: bool,
            ignore_keys=None,
            **gen_kwargs,
    ) -> tuple[Optional[float], Optional[torch.Tensor], Optional[torch.Tensor]]:  # 重写预测步骤方法

        with torch.no_grad():  # 确保不计算梯度
            if self.args.predict_with_generate:  # 如果使用生成方式预测
                output_ids = inputs.pop('output_ids')  # 提取并移除输出ID
            input_ids = inputs['input_ids']  # 获取输入ID

            loss, generated_tokens, labels = super().prediction_step(
                model, inputs, prediction_loss_only, ignore_keys, **gen_kwargs
            )  # 调用父类方法进行预测

            generated_tokens = generated_tokens[:, input_ids.size()[1]:]  # 去除输入部分，只保留生成部分
            labels = output_ids  # 使用之前提取的输出ID作为标签

            del inputs, input_ids, output_ids  # 删除不需要的变量释放内存
            torch.cuda.empty_cache()  # 清空CUDA缓存

        return loss, generated_tokens, labels  # 返回损失、生成的token和标签


@dc.dataclass  # 使用dataclass装饰器创建数据类
class DataConfig(object):  # 定义数据配置类
    train_file: Optional[str] = None  # 训练文件路径，默认为None
    val_file: Optional[str] = None  # 验证文件路径，默认为None
    test_file: Optional[str] = None  # 测试文件路径，默认为None
    num_proc: Optional[int] = None  # 处理器数量，默认为None

    @property
    def data_format(self) -> str:  # 定义数据格式属性
        return Path(self.train_file).suffix  # 返回训练文件的后缀名作为数据格式

    @property
    def data_files(self) -> dict[NamedSplit, str]:  # 定义数据文件属性
        return {
            split: data_file
            for split, data_file in zip(
                [Split.TRAIN, Split.VALIDATION, Split.TEST],  # 数据集分割类型
                [self.train_file, self.val_file, self.test_file],  # 对应的文件路径
            )
            if data_file is not None  # 只包含非空的文件路径
        }


@dc.dataclass  # 使用dataclass装饰器创建数据类
class FinetuningConfig(object):  # 定义微调配置类
    data_config: DataConfig  # 数据配置

    max_input_length: int  # 最大输入长度
    max_output_length: int  # 最大输出长度
    combine: bool  # 是否合并对话

    training_args: Seq2SeqTrainingArguments = dc.field(
        default_factory=lambda: Seq2SeqTrainingArguments(output_dir='./output')
    )  # 训练参数，默认输出到./output目录
    peft_config: Optional[PeftConfig] = None  # 参数高效微调配置，默认为None

    def __post_init__(self):  # 初始化后执行的方法
        if not self.training_args.do_eval or self.data_config.val_file is None:  # 如果不需要评估或没有验证文件
            self.training_args.do_eval = False  # 禁用评估
            self.training_args.evaluation_strategy = 'no'  # 设置评估策略为不评估
            self.data_config.val_file = None  # 清空验证文件路径
        else:  # 否则
            self.training_args.per_device_eval_batch_size = (
                    self.training_args.per_device_eval_batch_size
                    or self.training_args.per_device_train_batch_size
            )  # 设置每设备评估批量大小，如果未指定则使用训练批量大小

    @classmethod
    def from_dict(cls, **kwargs) -> 'FinetuningConfig':  # 从字典创建配置的类方法
        training_args = kwargs.get('training_args', None)  # 获取训练参数
        if training_args is not None and not isinstance(
                training_args, Seq2SeqTrainingArguments
        ):  # 如果训练参数存在且不是Seq2SeqTrainingArguments类型
            gen_config = training_args.get('generation_config')  # 获取生成配置
            if not isinstance(gen_config, GenerationConfig):  # 如果生成配置不是GenerationConfig类型
                training_args['generation_config'] = GenerationConfig(
                    **gen_config
                )  # 创建GenerationConfig对象
            kwargs['training_args'] = Seq2SeqTrainingArguments(**training_args)  # 创建Seq2SeqTrainingArguments对象

        data_config = kwargs.get('data_config')  # 获取数据配置
        if not isinstance(data_config, DataConfig):  # 如果数据配置不是DataConfig类型
            kwargs['data_config'] = DataConfig(**data_config)  # 创建DataConfig对象

        peft_config = kwargs.get('peft_config', None)  # 获取PEFT配置
        if peft_config is not None and not isinstance(peft_config, PeftConfig):  # 如果PEFT配置存在且不是PeftConfig类型
            kwargs['peft_config'] = get_peft_config(config_dict=peft_config)  # 获取PeftConfig对象
        return cls(**kwargs)  # 返回使用处理后的参数创建的配置对象

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> 'FinetuningConfig':  # 从文件创建配置的类方法
        path = Path(path)  # 转换路径为Path对象
        parser = yaml.YAML(typ='safe', pure=True)  # 创建YAML解析器
        parser.indent(mapping=2, offset=2, sequence=4)  # 设置缩进样式
        parser.default_flow_style = False  # 设置默认流样式为False
        kwargs = parser.load(path)  # 加载YAML文件
        return cls.from_dict(**kwargs)  # 使用加载的字典创建配置对象


def _load_datasets(
        data_dir: str,
        data_format: str,
        data_files: dict[NamedSplit, str],
        num_proc: Optional[int],
) -> DatasetDict:  # 加载数据集的内部函数
    if data_format == '.jsonl':  # 如果数据格式是jsonl
        dataset_dct = load_dataset(
            data_dir,
            data_files=data_files,
            split=None,
            num_proc=num_proc,
        )  # 使用Huggingface datasets加载数据集
    else:  # 如果是其他格式
        raise NotImplementedError(f"Cannot load dataset in the '{data_format}' format.")  # 抛出未实现错误
    return dataset_dct  # 返回数据集字典


class DataManager(object):  # 定义数据管理器类
    def __init__(self, data_dir: str, data_config: DataConfig):  # 初始化方法
        self._num_proc = data_config.num_proc  # 保存处理器数量

        self._dataset_dct = _load_datasets(
            data_dir,
            data_config.data_format,
            data_config.data_files,
            self._num_proc,
        )  # 加载数据集

    def _get_dataset(self, split: NamedSplit) -> Optional[Dataset]:  # 获取指定分割的数据集的内部方法
        return self._dataset_dct.get(split, None)  # 从数据集字典中获取指定分割的数据集

    def get_dataset(
            self,
            split: NamedSplit,
            process_fn: Callable[[dict[str, Any]], dict[str, Any]],
            batched: bool = True,
            remove_orig_columns: bool = True,
    ) -> Optional[Dataset]:  # 获取并处理数据集的方法
        orig_dataset = self._get_dataset(split)  # 获取原始数据集
        if orig_dataset is None:  # 如果数据集不存在
            return  # 返回None

        if remove_orig_columns:  # 如果需要移除原始列
            remove_columns = orig_dataset.column_names  # 获取所有列名
        else:  # 否则
            remove_columns = None  # 不移除任何列
        return orig_dataset.map(
            process_fn,
            batched=batched,
            remove_columns=remove_columns,
            num_proc=self._num_proc,
        )  # 使用提供的处理函数映射数据集


def process_message(message):  # 处理消息的函数
    if 'tools' in message and message['role'] == 'system':  # 如果消息中有tools字段且角色是system
        for tool in message['tools']:  # 遍历所有工具
            parameters = tool['function']['parameters']['properties']  # 获取参数属性
            tool['function']['parameters']['properties'] = \
                {k: v for k, v in parameters.items() if
                 v is not None}  # 过滤掉值为None的参数
    elif 'tools' in message:  # 如果消息中有tools字段但角色不是system
        del message['tools']  # 删除tools字段
    return message  # 返回处理后的消息


def process_batch(
        batch: Mapping[str, Sequence],
        tokenizer: PreTrainedTokenizer,
        max_input_length: int,
        max_output_length: int,
        combine: bool,
) -> dict[str, list]:  # 处理批次数据的函数
    batched_conv = batch['messages']  # 获取消息批次
    batched_input_ids = []  # 初始化输入ID列表
    batched_labels = []  # 初始化标签列表
    for conv in batched_conv:  # 遍历每个对话
        input_ids = [151331, 151333]  # 初始化输入ID为开始标记
        loss_masks = [False, False]  # 初始化损失掩码
        if combine:  # 如果合并对话
            new_input_ids = tokenizer.apply_chat_template(conv, tokenize=True, return_dict=False)  # 应用聊天模板
            input_ids = new_input_ids  # 更新输入ID
            loss_masks = [False] * len(input_ids)  # 初始化所有位置为False的损失掩码
            last_assistant_index = len(input_ids) - input_ids[::-1].index(151337) - 1  # 找到最后一个助手标记的位置
            for j in range(last_assistant_index + 1, len(input_ids)):  # 遍历助手回复部分
                loss_masks[j] = True  # 设置为计算损失的位置
        else:  # 如果不合并对话
            for message in conv:  # 遍历每条消息
                message = process_message(message)  # 处理消息
                loss_mask_val = False if message['role'] in ('system', 'user', 'observation') else True  # 确定损失掩码值
                new_input_ids = tokenizer.apply_chat_template([message], tokenize=True, return_dict=False)[2:]  # 应用聊天模板
                input_ids += new_input_ids  # 添加到输入ID
                loss_masks += [loss_mask_val] * len(new_input_ids)  # 添加对应的损失掩码

        input_ids.append(151336)  # 添加EOS标记
        loss_masks = [False, *loss_masks]  # 在损失掩码前添加一个False
        labels = []  # 初始化标签列表
        for input_id, mask in zip(input_ids, loss_masks):  # 遍历输入ID和损失掩码
            if mask:  # 如果需要计算损失
                labels.append(input_id)  # 将输入ID作为标签
            else:  # 否则
                labels.append(-100)  # 使用-100表示不计算损失的位置
        max_length = max_input_length + max_output_length + 1  # 计算最大长度
        batched_input_ids.append(input_ids[:max_length])  # 截断并添加到批次输入ID
        batched_labels.append(labels[:max_length])  # 截断并添加到批次标签

    del batched_conv, conv, input_ids, loss_masks, new_input_ids, labels  # 删除不需要的变量释放内存
    torch.cuda.empty_cache()  # 清空CUDA缓存

    return {'input_ids': batched_input_ids, 'labels': batched_labels}  # 返回处理后的批次数据


def process_batch_eval(
        batch: Mapping[str, Sequence],
        tokenizer: PreTrainedTokenizer,
        max_input_length: int,
        max_output_length: int,
        combine: bool,
) -> dict[str, list]:  # 处理评估批次数据的函数
    batched_conv = batch['messages']  # 获取消息批次
    batched_input_ids = []  # 初始化输入ID列表
    batched_output_ids = []  # 初始化输出ID列表

    for conv in batched_conv:  # 遍历每个对话
        if combine:  # 如果合并对话
            new_input_ids = tokenizer.apply_chat_template(conv, tokenize=True, return_dict=False)  # 应用聊天模板
            input_ids = new_input_ids  # 更新输入ID
            last_assistant_index = len(input_ids) - input_ids[::-1].index(151337) - 1  # 找到最后一个助手标记的位置
            output_prompt, output_ids = (
                input_ids[:1],
                input_ids[last_assistant_index:],
            )  # 分离输出提示和输出ID
            output_ids.append(151336)  # 添加EOS标记
            batched_input_ids.append(
                input_ids[:max_input_length] + output_prompt[:1]
            )  # 添加截断的输入ID和输出提示
            batched_output_ids.append(output_ids[:max_output_length])  # 添加截断的输出ID
        else:  # 如果不合并对话
            input_ids = [151331, 151333]  # 初始化输入ID为开始标记
            for message in conv:  # 遍历每条消息
                if len(input_ids) >= max_input_length:  # 如果输入ID长度已达到最大值
                    break  # 跳出循环
                else:  # 否则
                    message = process_message(message)  # 处理消息
                    new_input_ids = tokenizer.apply_chat_template([message], tokenize=True, return_dict=False)[2:]  # 应用聊天模板
                    if message['role'] == 'assistant':  # 如果是助手消息
                        output_prompt, output_ids = (
                            new_input_ids[:1],
                            new_input_ids[1:],
                        )  # 分离输出提示和输出ID
                        output_ids.append(151336)  # 添加EOS标记
                        batched_input_ids.append(
                            input_ids[:max_input_length] + output_prompt[:1]
                        )  # 添加截断的输入ID和输出提示
                        batched_output_ids.append(output_ids[:max_output_length])  # 添加截断的输出ID
                    input_ids += new_input_ids  # 更新输入ID

    del batched_conv, conv, input_ids, new_input_ids, output_prompt, output_ids  # 删除不需要的变量释放内存
    torch.cuda.empty_cache()  # 清空CUDA缓存

    return {'input_ids': batched_input_ids, 'output_ids': batched_output_ids}  # 返回处理后的批次数据


def load_tokenizer_and_model(
        model_dir: str,
        peft_config: Optional[PeftConfig] = None,
):  # 加载分词器和模型的函数
    tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)  # 加载预训练分词器
    if peft_config is not None:  # 如果有PEFT配置
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            trust_remote_code=True,
            empty_init=False,
            use_cache=False,
            torch_dtype=torch.bfloat16  # Must use BFloat 16
        )  # 加载预训练模型
        model = get_peft_model(model, peft_config)  # 应用PEFT配置
        model.print_trainable_parameters()  # 打印可训练参数信息
    else:  # 如果没有PEFT配置
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            trust_remote_code=True,
            empty_init=False,
            use_cache=False,
            torch_dtype=torch.bfloat16
        )  # 加载预训练模型
    return tokenizer, model  # 返回分词器和模型


def compute_metrics(eval_preds: EvalPrediction, tokenizer):  # 计算评估指标的函数
    batched_pred_ids, batched_label_ids = eval_preds  # 获取预测ID和标签ID
    metrics_dct = {'rouge-1': [], 'rouge-2': [], 'rouge-l': [], 'bleu-4': []}  # 初始化指标字典
    for pred_ids, label_ids in zip(batched_pred_ids, batched_label_ids):  # 遍历每对预测和标签
        pred_txt = tokenizer.decode(pred_ids).strip()  # 解码预测ID
        label_txt = tokenizer.decode(label_ids).strip()  # 解码标签ID
        pred_tokens = list(jieba.cut(pred_txt))  # 对预测文本分词
        label_tokens = list(jieba.cut(label_txt))  # 对标签文本分词
        rouge = Rouge()  # 创建Rouge评估器
        scores = rouge.get_scores(' '.join(pred_tokens), ' '.join(label_tokens))  # 计算Rouge分数
        for k, v in scores[0].items():  # 遍历每个Rouge指标
            metrics_dct[k].append(round(v['f'] * 100, 4))  # 添加F1分数
        metrics_dct['bleu-4'].append(
            sentence_bleu([label_tokens], pred_tokens, smoothing_function=SmoothingFunction().method3))  # 计算BLEU-4分数
    return {k: np.mean(v) for k, v in metrics_dct.items()}  # 返回每个指标的平均值


@app.command()  # 注册为Typer应用的命令
def main(
        data_dir: Annotated[str, typer.Argument(help='')],  # 数据目录参数
        model_dir: Annotated[
            str,
            typer.Argument(
                help='A string that specifies the model id of a pretrained model configuration hosted on huggingface.co, or a path to a directory containing a model configuration file.'
            ),
        ],  # 模型目录参数
        config_file: Annotated[str, typer.Argument(help='')],  # 配置文件参数
        auto_resume_from_checkpoint: str = typer.Argument(
            default='',
            help='If entered as yes, automatically use the latest save checkpoint. If it is a numerical example 12 15, use the corresponding save checkpoint. If the input is no, restart training'
        ),  # 自动从检查点恢复参数
):
    ft_config = FinetuningConfig.from_file(config_file)  # 从文件加载微调配置
    tokenizer, model = load_tokenizer_and_model(model_dir, peft_config=ft_config.peft_config)  # 加载分词器和模型
    data_manager = DataManager(data_dir, ft_config.data_config)  # 创建数据管理器

    train_dataset = data_manager.get_dataset(
        Split.TRAIN,
        functools.partial(
            process_batch,
            tokenizer=tokenizer,
            combine=ft_config.combine,
            max_input_length=ft_config.max_input_length,
            max_output_length=ft_config.max_output_length,
        ),
        batched=True,
    )  # 获取训练数据集
    print('train_dataset:', train_dataset)  # 打印训练数据集信息
    val_dataset = data_manager.get_dataset(
        Split.VALIDATION,
        functools.partial(
            process_batch_eval,
            tokenizer=tokenizer,
            combine=ft_config.combine,
            max_input_length=ft_config.max_input_length,
            max_output_length=ft_config.max_output_length,
        ),
        batched=True,
    )  # 获取验证数据集
    if val_dataset is not None:  # 如果验证数据集存在
        print('val_dataset:', val_dataset)  # 打印验证数据集信息
    test_dataset = data_manager.get_dataset(
        Split.TEST,
        functools.partial(
            process_batch_eval,
            tokenizer=tokenizer,
            combine=ft_config.combine,
            max_input_length=ft_config.max_input_length,
            max_output_length=ft_config.max_output_length,
        ),
        batched=True,
    )  # 获取测试数据集
    if test_dataset is not None:  # 如果测试数据集存在
        print('test_dataset:', test_dataset)  # 打印测试数据集信息

    model.gradient_checkpointing_enable()  # 启用梯度检查点以节省内存
    model.enable_input_require_grads()  # 启用输入需要梯度
    
    ft_config.training_args.generation_config.pad_token_id = (
        151329
    )  # 设置生成配置的填充token ID
    ft_config.training_args.generation_config.eos_token_id = [
        151329, 151336, 151338
    ]  # 设置生成配置的结束token ID列表

    trainer = Seq2SeqTrainer(
        model=model,
        args=ft_config.training_args,
        data_collator=DataCollatorForSeq2Seq(
            tokenizer=tokenizer,
            padding='longest',
            return_tensors='pt',
        ),
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=functools.partial(compute_metrics, tokenizer=tokenizer),
    )  # 创建训练器

    if auto_resume_from_checkpoint.upper() == "" or auto_resume_from_checkpoint is None:  # 如果不需要从检查点恢复
        trainer.train()  # 开始训练
    else:  # 如果需要从检查点恢复
    if auto_resume_from_checkpoint.upper() == "" or auto_resume_from_checkpoint is None:
        trainer.train()
    else:
        output_dir = ft_config.training_args.output_dir
        dirlist = os.listdir(output_dir)
        checkpoint_sn = 0
        for checkpoint_str in dirlist:
            if checkpoint_str.find("eckpoint") > 0 and checkpoint_str.find("tmp") == -1:
                checkpoint = int(checkpoint_str.replace("checkpoint-", ""))
                if checkpoint > checkpoint_sn:
                    checkpoint_sn = checkpoint
        if auto_resume_from_checkpoint.upper() == "YES":
            if checkpoint_sn > 0:
                model.gradient_checkpointing_enable()
                model.enable_input_require_grads()
                checkpoint_directory = os.path.join(output_dir, "checkpoint-" + str(checkpoint_sn))
                print("resume checkpoint from checkpoint-" + str(checkpoint_sn))
                trainer.train(resume_from_checkpoint=checkpoint_directory)
            else:
                trainer.train()
        else:
            if auto_resume_from_checkpoint.isdigit():
                if int(auto_resume_from_checkpoint) > 0:
                    checkpoint_sn = int(auto_resume_from_checkpoint)
                    model.gradient_checkpointing_enable()
                    model.enable_input_require_grads()
                    checkpoint_directory = os.path.join(output_dir, "checkpoint-" + str(checkpoint_sn))
                    print("resume checkpoint from checkpoint-" + str(checkpoint_sn))
                    trainer.train(resume_from_checkpoint=checkpoint_directory)
            else:
                print(auto_resume_from_checkpoint,
                      "The specified checkpoint sn(" + auto_resume_from_checkpoint + ") has not been saved. Please search for the correct checkpoint in the model output directory")

    if test_dataset is not None:
        trainer.predict(test_dataset)


if __name__ == '__main__':
    app()
