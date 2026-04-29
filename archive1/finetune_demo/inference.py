# 导入Path类，用于处理文件路径
from pathlib import Path
# 导入类型注解工具
from typing import Annotated, Union
# 导入typer库，用于创建命令行应用
import typer
# 从peft模块导入PeftModelForCausalLM，用于加载LoRA等参数高效微调模型
from peft.peft_model import PeftModelForCausalLM
# 导入transformers库中的模型和分词器
from transformers import (
    AutoModel,
    AutoTokenizer,
)
# 导入PIL的Image类，用于处理图像
from PIL import Image
# 导入torch库
import torch

# 创建一个typer应用，用于命令行交互
app = typer.Typer(pretty_exceptions_show_locals=False)


# 定义加载模型和分词器的函数
def load_model_and_tokenizer(
        model_dir: Union[str, Path], trust_remote_code: bool = True
):
    # 将模型路径转换为绝对路径
    model_dir = Path(model_dir).expanduser().resolve()
    # 检查是否存在adapter配置文件，判断是否为LoRA微调模型
    if (model_dir / 'adapter_config.json').exists():
        # 导入json模块
        import json
        # 读取adapter配置文件
        with open(model_dir / 'adapter_config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        # 加载基础模型
        model = AutoModel.from_pretrained(
            config.get('base_model_name_or_path'),
            trust_remote_code=trust_remote_code,
            device_map='auto',  # 自动分配到可用设备
            torch_dtype=torch.bfloat16  # 使用bfloat16精度
        )
        # 加载LoRA适配器权重
        model = PeftModelForCausalLM.from_pretrained(
            model=model,
            model_id=model_dir,
            trust_remote_code=trust_remote_code,
        )
        # 获取分词器目录，指向基础模型
        tokenizer_dir = model.peft_config['default'].base_model_name_or_path
    else:
        # 如果不是LoRA模型，直接加载完整模型
        model = AutoModel.from_pretrained(
            model_dir,
            trust_remote_code=trust_remote_code,
            device_map='auto',
            torch_dtype=torch.bfloat16
        )
        # 分词器目录与模型目录相同
        tokenizer_dir = model_dir
    # 加载分词器
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir,
        trust_remote_code=trust_remote_code,
        encode_special_tokens=True,  # 编码特殊标记
        use_fast=False  # 不使用快速分词器
    )
    # 返回模型和分词器
    return model, tokenizer


# 定义主函数，使用typer装饰器注册为命令
@app.command()
def main(
        model_dir: Annotated[str, typer.Argument(help='')],  # 模型目录参数
):
    # 为GLM-4微调（不带工具）准备的消息
    messages = [
        {
            "role": "user", "content": "#裙子#夏天",  # 用户输入的提示
        }
    ]

    # 为GLM-4微调（带工具）准备的消息，目前被注释
    # messages = [
    #     {
    #         "role": "system", "content": "",
    #         "tools":
    #             [
    #                 {
    #                     "type": "function",
    #                     "function": {
    #                         "name": "create_calendar_event",
    #                         "description": "Create a new calendar event",
    #                         "parameters": {
    #                             "type": "object",
    #                             "properties": {
    #                                 "title": {
    #                                     "type": "string",
    #                                     "description": "The title of the event"
    #                                 },
    #                                 "start_time": {
    #                                     "type": "string",
    #                                     "description": "The start time of the event in the format YYYY-MM-DD HH:MM"
    #                                 },
    #                                 "end_time": {
    #                                     "type": "string",
    #                                     "description": "The end time of the event in the format YYYY-MM-DD HH:MM"
    #                                 }
    #                             },
    #                             "required": [
    #                                 "title",
    #                                 "start_time",
    #                                 "end_time"
    #                             ]
    #                         }
    #                     }
    #                 }
    #             ]
    #
    #     },
    #     {
    #         "role": "user",
    #         "content": "Can you help me create a calendar event for my meeting tomorrow? The title is \"Team Meeting\". It starts at 10:00 AM and ends at 11:00 AM."
    #     },
    # ]

    # 为GLM-4V微调（多模态）准备的消息，目前被注释
    # messages = [
    #     {
    #         "role": "user",
    #         "content": "女孩可能希望观众做什么？",
    #         "image": Image.open("your Image").convert("RGB")  # 加载并转换图像
    #     }
    # ]

    # 加载模型和分词器
    model, tokenizer = load_model_and_tokenizer(model_dir)
    # 应用聊天模板处理消息，转换为模型输入格式
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,  # 添加生成提示
        tokenize=True,  # 进行分词
        return_tensors="pt",  # 返回PyTorch张量
        return_dict=True  # 返回字典格式
    ).to(model.device)  # 将输入移至模型所在设备
    # 设置生成参数
    generate_kwargs = {
        "max_new_tokens": 1024,  # 最大生成标记数
        "do_sample": True,  # 使用采样
        "top_p": 0.8,  # top-p采样参数
        "temperature": 0.8,  # 温度参数，控制随机性
        "repetition_penalty": 1.2,  # 重复惩罚
        "eos_token_id": model.config.eos_token_id,  # 结束标记ID
    }
    # 打印模型信息
    print(model)
    # 生成回复
    outputs = model.generate(**inputs, **generate_kwargs)
    # 解码生成的标记，跳过输入部分，只保留模型生成的回复
    response = tokenizer.decode(outputs[0][len(inputs['input_ids'][0]):], skip_special_tokens=True).strip()
    # 打印分隔线
    print("=========")
    # 打印模型回复
    print(response)


# 程序入口点
if __name__ == '__main__':
    # 运行typer应用
    app()
