import torch.nn as nn
import torch
from torch.autograd import Variable
from config import config as cfg
from data.kitti import KittiDataset
import torch.utils.data as data
import time
from loss import VoxelLoss
from voxelnet import VoxelNet
import torch.optim as optim
import torch.nn.init as init

# from nms.pth_nms import pth_nms
from torchvision.ops import nms

import numpy as np
import torch.backends.cudnn
from test_utils import draw_boxes


from torch.utils.tensorboard import SummaryWriter
from torchvision import transforms



import cv2
def weights_init(m):
    if isinstance(m, nn.Conv2d):
        init.xavier_uniform(m.weight.data)
        m.bias.data.zero_()

def detection_collate(batch):
    voxel_features = []
    voxel_coords = []
    pos_equal_one = []
    neg_equal_one = []
    targets = []

    images = []
    calibs = []
    ids = []
    for i, sample in enumerate(batch):
        voxel_features.append(sample[0])

        voxel_coords.append(
            np.pad(sample[1], ((0, 0), (1, 0)),
                mode='constant', constant_values=i))

        pos_equal_one.append(sample[2])
        neg_equal_one.append(sample[3])
        targets.append(sample[4])

        images.append(sample[5])
        calibs.append(sample[6])
        ids.append(sample[7])
    return np.concatenate(voxel_features), \
           np.concatenate(voxel_coords), \
           np.array(pos_equal_one),\
           np.array(neg_equal_one),\
           np.array(targets),\
           images, calibs, ids

torch.backends.cudnn.enabled=True

# dataset
train_dataset=KittiDataset(cfg=cfg,root='/data/KITTI/training',set='train')
train_dataloader = data.DataLoader(train_dataset, batch_size=cfg.N, num_workers=4, collate_fn=detection_collate, shuffle=True, \
                              pin_memory=False)


# val_dataset=KittiDataset(cfg=cfg,root='/data/KITTI/validataion',set='val')
# val_dataloader = data.DataLoader(val_dataset, batch_size=cfg.N, num_workers=4, collate_fn=detection_collate, shuffle=True, \
#                               pin_memory=False)





# network
net = VoxelNet()
net.cuda()


#Note: Ammaar 
val_dataloader_iter = iter(train_dataloader)
voxel_features, voxel_coords, pos_equal_one, neg_equal_one, targets, images, calibs, ids = next(val_dataloader_iter)

# wrapping and moving data to GPU
# wrapper to variable
voxel_features = Variable(torch.cuda.FloatTensor(voxel_features))
voxel_tensor_coord =  Variable(torch.cuda.FloatTensor(voxel_coords))

with SummaryWriter(comment='VoxelNet') as w: 
    w.add_graph(net, [voxel_features, voxel_tensor_coord] , verbose=False)
    w.close()


print("function completed")
print("VoxelNet added into the graph")
    


def train():

    net.train()

    # initialization
    print('Initializing weights...')
    net.apply(weights_init)

    # define optimizer
    optimizer = optim.SGD(net.parameters(), lr=0.01)

    # define loss function
    criterion = VoxelLoss(alpha=1.5, beta=1)

    # training process
    batch_iterator = None
    epoch_size = len(dataset) // cfg.N
    print('Epoch size', epoch_size)
    
    for (i, data) in enumerate(train_dataloader):
            # if (not batch_iterator) or (iteration % epoch_size == 0):
            #     # create batch iterator
            #     batch_iterator = iter(data_loader)
            data = next(train_dataloader)

            voxel_features, voxel_coords, pos_equal_one, neg_equal_one, targets, images, calibs, ids = data

            # wrapper to variable
            voxel_features = Variable(torch.cuda.FloatTensor(voxel_features))
            pos_equal_one = Variable(torch.cuda.FloatTensor(pos_equal_one))
            neg_equal_one = Variable(torch.cuda.FloatTensor(neg_equal_one))
            targets = Variable(torch.cuda.FloatTensor(targets))

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward
            t0 = time.time()
            break
            psm,rm = net(voxel_features, voxel_coords)

            # calculate loss
            conf_loss, reg_loss = criterion(rm, psm, pos_equal_one, neg_equal_one, targets)
            loss = conf_loss + reg_loss

            # backward
            loss.backward()
            optimizer.step()

            t1 = time.time()


            print('Timer: %.4f sec.' % (t1 - t0))
            print('iter ' + repr(iteration) + ' || Loss: %.4f || Conf Loss: %.4f || Loc Loss: %.4f' % \
                  (loss.data[0], conf_loss.data[0], reg_loss.data[0]))

            # visualization
            #draw_boxes(rm, psm, ids, images, calibs, 'pred')
            draw_boxes(targets.data, pos_equal_one.data, images, calibs, ids,'true')



if __name__ == '__main__':
    train()