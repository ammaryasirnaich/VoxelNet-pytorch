import os
import torch
# from torch.utils.ffi import create_extension
from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

sources = ['src/nms.c']
headers = ['src/nms.h']
defines = []
with_cuda = False

if torch.cuda.is_available():
    print('Including CUDA code.')
    sources += ['src/nms_cuda.c']
    headers += ['src/nms_cuda.h']
    defines += [('WITH_CUDA', None)]
    with_cuda = True

this_file = os.path.dirname(os.path.realpath(__file__))
print(this_file)
extra_objects = ['src/cuda/nms_kernel.cu.o']
extra_objects = [os.path.join(this_file, fname) for fname in extra_objects]

# ffi = setup(
#     '_ext.nms',
#     headers=headers,
#     sources=sources,
#     define_macros=defines,
#     relative_to=__file__,
#     with_cuda=with_cuda,
#     extra_objects=extra_objects
# )


ffi = setup(
        name='cuda_extension',
        ext_modules=[
            CUDAExtension(
                    name='cuda_extension',
                    sources=['src/nms_cuda.c', 'src/cuda/nms_kernel.cu.o'],
                    extra_compile_args={'cxx': ['-g'],
                                        'nvcc': ['-O2']})
        ],
        cmdclass={
            'build_ext': BuildExtension
        })

if __name__ == '__main__':
    ffi.build()
