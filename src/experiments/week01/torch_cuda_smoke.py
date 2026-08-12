from __future__ import annotations

from pathlib import Path

import torch


OUT_DIR = Path.home() / "week01_habitat_evidence"
OUT_DIR.mkdir(exist_ok=True)

lines = [
    "PyTorch CUDA smoke test",
    f"torch: {torch.__version__}",
    f"cuda_available: {torch.cuda.is_available()}",
    f"cuda_version: {torch.version.cuda}",
    f"device_count: {torch.cuda.device_count()}",
]

if torch.cuda.is_available():
    device = torch.device("cuda:0")
    a = torch.arange(9, dtype=torch.float32, device=device).reshape(3, 3)
    b = torch.eye(3, dtype=torch.float32, device=device)
    c = a @ b
    torch.cuda.synchronize()
    lines.extend(
        [
            f"device_name: {torch.cuda.get_device_name(0)}",
            f"tensor_device: {c.device}",
            f"tensor_sum: {float(c.sum().item())}",
            "result: ok",
        ]
    )
else:
    lines.append("result: failed")
    raise SystemExit("\n".join(lines))

output = OUT_DIR / "torch_cuda_smoke.txt"
output.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
print(f"saved: {output}")
