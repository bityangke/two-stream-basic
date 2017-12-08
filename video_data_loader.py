import numpy as np
import os
import torch
import torch.utils.data as data
import scipy.io as io
import pickle
import time
import torchvision.transforms as trans
import random
from multiprocessing import Pool
from PIL import Image


class ucf101_rgb_loader_basic(data.Dataset):
    def __init__(self, data_dir, file_dir, data_type, image_size=224):
        self.data_type = data_type
        self.data_dir = data_dir  # data_dir = /home/yongyi/ucf101_train/my_code/data
        self.file_dir = file_dir  # file_dir = /home/local/yongyi/...
        self.image_size = image_size
        self.size_all = [256, 224, 192, 168]  # 4 different length for width and height following TSN.

        if self.data_type == 'train':
            with open(os.path.join(self.data_dir, 'train_name.pkl'), 'r') as f:
                self.data_name_list = pickle.load(f)
            with open(os.path.join(self.data_dir, 'train_nFrames.pkl'), 'r') as f:
                self.nFrame_list = pickle.load(f)
            with open(os.path.join(self.data_dir, 'train_label.pkl'), 'r') as f:
                self.label_list = pickle.load(f)
            self.transform = None

        elif self.data_type == 'test':
            with open(os.path.join(self.data_dir, 'test_name.pkl'), 'r') as f:
                self.data_name_list = pickle.load(f)
            with open(os.path.join(self.data_dir, 'test_nFrames.pkl'), 'r') as f:
                self.nFrame_list = pickle.load(f)
            with open(os.path.join(self.data_dir, 'test_label.pkl'), 'r') as f:
                self.label_list = pickle.load(f)
            self.transform = trans.Compose([trans.Scale(256),
                                            trans.TenCrop(self.image_size),
                                            trans.Lambda(lambda crops:
                                            torch.stack([trans.ToTensor()(trans.Resize(self.image_size)(crop)) for crop in crops]))])

        else:
            raise('Error data_type')

    def __getitem__(self, index):
        # Read a list of image by index
        target = self.label_list[index:index+1, :]
        target = torch.from_numpy(target)  # size: (1, 101) 101 classes for ucf101
        # One image example
        file_name = self.data_name_list[index]
        """
        Currently random select one frame; TODO: TSN
        """
        image_index = random.randint(1, self.nFrame_list[index])
        img_dir = os.path.join(self.file_dir, file_name, ('frame' + '%06d' % image_index + '.jpg'))
        img = Image.open(img_dir).convert('RGB')

        # Perform transform
        # Scale jittering
        width_rand = self.size_all[random.randint(0, 3)]
        height_rand = self.size_all[random.randint(0, 3)]
        crop_size = (height_rand, width_rand)

        if self.transform is None:
            transform = trans.Compose([trans.Scale(256),
                                      trans.TenCrop(crop_size),
                                      trans.Lambda(lambda crops:
                                      torch.stack([trans.ToTensor()(trans.Resize(self.image_size)(crop)) for crop in crops]))])
        else:
            transform = self.transform

        img = transform(img)

        # Return image and target
        return img, target

    def __len__(self):
        return len(self.data_name_list)


class ucf101_rgb_loader_tsn(data.Dataset):
    def __init__(self, data_dir, file_dir, data_type, image_size=224, tsn_num=3):
        self.data_type = data_type
        self.data_dir = data_dir  # data_dir = /home/yongyi/ucf101_train/my_code/data
        self.file_dir = file_dir  # file_dir = /home/local/yongyi/...
        self.image_size = image_size
        self.size_all = [256, 224, 192, 168]  # 4 different length for width and height following TSN.\
        self.tsn_num = tsn_num  # The number of segmentations for a video.

        if self.data_type == 'train':
            with open(os.path.join(self.data_dir, 'train_name.pkl'), 'r') as f:
                self.data_name_list = pickle.load(f)
            with open(os.path.join(self.data_dir, 'train_nFrames.pkl'), 'r') as f:
                self.nFrame_list = pickle.load(f)
            with open(os.path.join(self.data_dir, 'train_label.pkl'), 'r') as f:
                self.label_list = pickle.load(f)
            self.transform = None

        elif self.data_type == 'test':
            with open(os.path.join(self.data_dir, 'test_name.pkl'), 'r') as f:
                self.data_name_list = pickle.load(f)
            with open(os.path.join(self.data_dir, 'test_nFrames.pkl'), 'r') as f:
                self.nFrame_list = pickle.load(f)
            with open(os.path.join(self.data_dir, 'test_label.pkl'), 'r') as f:
                self.label_list = pickle.load(f)
            self.transform = trans.Compose([trans.Scale(256),
                                            trans.TenCrop(self.image_size),
                                            trans.Lambda(lambda crops:
                                            torch.stack([trans.ToTensor()(trans.Resize(self.image_size)(crop)) for crop in crops]))])

        else:
            raise('Error data_type')

    def __getitem__(self, index):
        # Read a list of image by index
        target = self.label_list[index:index+1, :]
        target = torch.from_numpy(target)  # size: (1, 101) 101 classes for ucf101
        # One image example
        file_name = self.data_name_list[index]
        """
        Currently random select one frame; TODO: TSN
        """
        seg_len = int(self.nFrame_list[index] / self.tsn_num)
        image_list = []
        for i in range(self.tsn_num):
            image_index = random.randint(1 + i * seg_len, (i + 1) * seg_len)
            img_dir = os.path.join(self.file_dir, file_name, ('frame' + '%06d' % image_index + '.jpg'))
            img = Image.open(img_dir).convert('RGB')
            image_list.append(img)

        # Perform transform
        # Scale jittering
        width_rand = self.size_all[random.randint(0, 3)]
        height_rand = self.size_all[random.randint(0, 3)]
        crop_size = (height_rand, width_rand)

        if self.transform is None:
            transform = trans.Compose([trans.Scale(256),
                                      trans.TenCrop(crop_size),
                                      trans.Lambda(lambda crops:
                                      torch.stack([trans.ToTensor()(trans.Resize(self.image_size)(crop)) for crop in crops]))])
        else:
            transform = self.transform

        img_tensor = torch.stack([transform(img) for img in image_list])  # size (self.tsn_num, 10, 3, 224, 224)

        # Return image and target
        return img_tensor, target

    def __len__(self):
        return len(self.data_name_list)


def process_data_from_mat():
    # Read data from mat
    data_dir = '/home/yongyi/ucf101_train/my_code/data'
    name = io.loadmat(os.path.join(data_dir, 'name.mat'))['name']
    label = io.loadmat(os.path.join(data_dir, 'label.mat'))['label']
    one_hot_label = io.loadmat(os.path.join(data_dir, 'one_hot_label.mat'))['one_hot_label']
    data_set = io.loadmat(os.path.join(data_dir, 'set.mat'))['set']
    nFrames = io.loadmat(os.path.join(data_dir, 'nFrames.mat'))['nFrames']

    nObject = name.shape[1]
    train_nObject = np.sum(data_set == 1)
    test_nObject = np.sum(data_set == 2)

    name_list = []
    for i in xrange(nObject):
        a = name[0, i].tolist()
        b = str(a[0])  # example: 'v_ApplyEyeMakeup_g08_c01.avi'
        fname, back = b.split('.')
        name_list.append(fname)  # example: 'v_ApplyEyeMakeup_g08_c01'

    train_name = name_list[:train_nObject]
    test_name = name_list[train_nObject:]

    train_label = one_hot_label[:train_nObject, :]
    test_label = one_hot_label[train_nObject:, :]

    train_nFrames = nFrames[0, :train_nObject]
    test_nFrames = nFrames[0, train_nObject:]

    train_index = label[0, :train_nObject]
    test_index = label[0, train_nObject:]

    f = open(os.path.join(data_dir, 'train_name.pkl'), 'wb')
    pickle.dump(train_name, f)
    f.close()
    f = open(os.path.join(data_dir, 'test_name.pkl'), 'wb')
    pickle.dump(test_name, f)
    f.close()
    f = open(os.path.join(data_dir, 'train_label.pkl'), 'wb')
    pickle.dump(train_label, f)
    f.close()
    f = open(os.path.join(data_dir, 'test_label.pkl'), 'wb')
    pickle.dump(test_label, f)
    f.close()
    f = open(os.path.join(data_dir, 'train_nFrames.pkl'), 'wb')
    pickle.dump(train_nFrames, f)
    f.close()
    f = open(os.path.join(data_dir, 'test_nFrames.pkl'), 'wb')
    pickle.dump(test_nFrames, f)
    f.close()
    f = open(os.path.join(data_dir, 'train_index.pkl'), 'wb')
    pickle.dump(train_index, f)
    f.close()
    f = open(os.path.join(data_dir, 'test_index.pkl'), 'wb')
    pickle.dump(test_index, f)
    f.close()