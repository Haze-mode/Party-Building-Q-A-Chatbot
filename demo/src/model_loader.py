from pathlib import Path
from typing import Union, Optional
import torch
from peft import AutoPeftModelForCausalLM, PeftModelForCausalLM
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
)

ModelType = Union[PreTrainedModel, PeftModelForCausalLM]
TokenizerType = Union[PreTrainedTokenizer, PreTrainedTokenizerFast]

def load_model_and_tokenizer(
    model_dir: Union[str, Path],
    trust_remote_code: bool = True,
    device_map: str = "auto",
    torch_dtype: torch.dtype = torch.float16,   # 使用半精度减少显存占用
    max_memory: Optional[dict] = None,
):
    """
    加载模型和分词器，自动适配 PEFT 微调模型。
    
    注意：已移除 bitsandbytes 8bit/4bit 量化加载，改用 torch.float16 加载，
         以解决 bitsandbytes 与当前 CUDA/triton 环境不兼容的问题。
    
    Args:
        model_dir: 模型或 adapter 目录路径
        trust_remote_code: 是否信任远程代码
        device_map: 设备映射策略，默认为 "auto"
        torch_dtype: 模型加载时的数据类型，默认 torch.float16
        max_memory: 每个设备的显存上限字典，例如 {0: "10GiB", "cpu": "30GiB"}
    
    Returns:
        (model, tokenizer)
    """
    model_dir = Path(model_dir).expanduser().resolve()

    # 通用加载参数
    common_kwargs = dict(
        trust_remote_code=trust_remote_code,
        device_map=device_map,
        torch_dtype=torch_dtype,
        max_memory=max_memory,
    )

    if (model_dir / 'adapter_config.json').exists():
        # 加载 PEFT 微调模型
        model = AutoPeftModelForCausalLM.from_pretrained(
            model_dir,
            **common_kwargs
        )
        # 分词器目录优先使用基座模型路径（adapter 可能不包含 tokenizer）
        tokenizer_dir = model.peft_config['default'].base_model_name_or_path
    else:
        # 加载普通完整模型
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            **common_kwargs
        )
        tokenizer_dir = model_dir

    # 加载分词器
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_dir,
        trust_remote_code=trust_remote_code,
        encode_special_tokens=True,
        use_fast=False
    )
    
    return model, tokenizer