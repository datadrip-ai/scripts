::Hardware detection issues

Check for loose power cables, ensure the card is receiving voltage and seated fully in the socket.
Download the latest software drivers for your GPU with a clean install:

https://www.nvidia.com/en-us/drivers/

Install and restart

Verify the device is recognized and drivers are current in Device Manager:

control /name Microsoft.DeviceManager

Python configuration

Torch requires Python 3.9 or later.
Change directory to your Comfy install folder and activate the virtual environment:

cd c:\comfyui\.venv\scripts && activate

Verify Python is on PATH and satisfies the requirements:

where python && python --version

Example output:

c:\ComfyUI\.venv\Scripts\python.exe  
C:\Python313\python.exe  
C:\Python310\python.exe  
Python 3.12.9  

Your terminal checks the PATH inside the .venv folder first, then checks user variable paths. If you aren't inside the virtual environment, you may see different results. If issues persist here, back up folders and do a clean Comfy install to correct Python environment issues before proceeding,

Update pip:

python -m pip install --upgrade pip

Check for inconsistencies in your current environment:

pip check

Expected output:

No broken requirements found.

Err #1: CUDA version incompatible

Error message:

CUDA error: no kernel image is available for execution on the device  
CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.  
For debugging consider passing CUDA_LAUNCH_BLOCKING=1  
Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.  

Configuring CUDA

Uninstall any old versions of CUDA in Windows Program Manager.
Delete all CUDA paths from environmental variables and program folders.
Check CUDA requirements for your GPU (inside venv):

nvidia-smi

Example output:

+-----------------------------------------------------------------------------------------+  
| NVIDIA-SMI 576.02                 Driver Version: 576.02         CUDA Version: 12.9     |  
|-----------------------------------------+------------------------+----------------------+  
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |  
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |  
|                                         |                        |               MIG M. |  
|=========================================+========================+======================|  
|   0  NVIDIA GeForce RTX 5070      WDDM  |   00000000:01:00.0  On |                  N/A |  
|  0%   31C    P8             10W /  250W |    1003MiB /  12227MiB |      6%      Default |  
|                                         |                        |                  N/A |  
+-----------------------------------------+------------------------+----------------------+  

Example: RTX 5070 reports CUDA version 12.9 is required.
Find your device on the CUDA Toolkit Archive and install:

https://developer.nvidia.com/cuda-toolkit-archive

Change working directory to ComfyUI install location and activate the virtual environment:

cd C:\ComfyUI\.venv\Scripts && activate

Check that the CUDA compiler tool is visible in the virtual environment:

where nvcc

Expected output:

C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9\bin\nvcc.exe

If not found, locate the CUDA folder on disk and copy the path:

C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9

Add CUDA folder paths to the user PATH variable using the Environmental Variables in the Control Panel:

C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9  
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9\bin

Refresh terminal and verify:

refreshenv && where nvcc

Check that the correct native Python libraries are installed:

pip list | findstr cuda

Example output:

cuda-bindings              12.9.0  
cuda-python                12.9.0  
nvidia-cuda-runtime-cu12   12.8.90  

If outdated (e.g., 12.8.90), uninstall and install the correct version:

pip uninstall -y nvidia-cuda-runtime-cu12  
pip install nvidia-cuda-runtime-cu12  

Verify installation:

pip show nvidia-cuda-runtime-cu12

Expected output:

Name: nvidia-cuda-runtime-cu12  
Version: 12.9.37  
Summary: CUDA Runtime native Libraries  
Home-page: https://developer.nvidia.com/cuda-zone  
Author: Nvidia CUDA Installer Team  
Author-email: compute_installer@nvidia.com  
License: NVIDIA Proprietary Software  
Location: C:\ComfyUI\.venv\Lib\site-packages  
Requires:  
Required-by: tensorrt_cu12_libs  

Err #2: PyTorch version incompatible

Comfy warns on launch:

NVIDIA GeForce RTX 5070 with CUDA capability sm_120 is not compatible with the current PyTorch installation.  
The current PyTorch install supports CUDA capabilities sm_50 sm_60 sm_61 sm_70 sm_75 sm_80 sm_86 sm_90.  
If you want to use the NVIDIA GeForce RTX 5070 GPU with PyTorch, please check the instructions at https://pytorch.org/get-started/locally/  

Configuring Python packages

Check current PyTorch, TorchVision, TorchAudio, NVIDIA, and Python versions:

pip list | findstr torch

Example output:

open_clip_torch            2.32.0  
torch                      2.6.0+cu126  
torchaudio                 2.6.0+cu126  
torchsde                   0.2.6  
torchvision                0.21.0+cu126  

If using cu126 (incompatible), uninstall and install cu128 (nightly release supports Blackwell architecture):

pip uninstall -y torch torchaudio torchvision  
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128  

Verify installation:

pip list | findstr torch

Expected output:

open_clip_torch            2.32.0  
torch                      2.8.0.dev20250518+cu128  
torchaudio                 2.6.0.dev20250519+cu128  
torchsde                   0.2.6  
torchvision                0.22.0.dev20250519+cu128  

Resources

NVIDIA

    CUDA compatibility list: https://developer.nvidia.com/cuda-gpus

    Native libraries resources: https://nvidia.github.io/cuda-python/latest/

    CUDA install guide: https://docs.nvidia.com/cuda/cuda-installation-guide-microsoft-windows/

    Deep learning framework matrix: https://docs.nvidia.com/deeplearning/frameworks/support-matrix/index.html

Torch

    PyTorch archive: https://pytorch.org/get-started/previous-versions/

    Torch documentation: https://pypi.org/project/torch/

Python

    Download Python: https://www.python.org/downloads/

    Python package index and docs: https://pypi.org/

    Pip docs: https://pip.pypa.io/en/latest/user_guide/

Comfy/Models

    Comfy Wiki: https://comfyui-wiki.com/en

    Comfy GitHub: https://github.com/comfyanonymous/ComfyUI
