import os
from torch_geometric.data import InMemoryDataset
from torch_geometric import data as DATA
import torch


class TestbedDataset(InMemoryDataset):
    def __init__(self,
                 root='/tmp',
                 dataset='davis',
                 xd=None,
                 xt=None,
                 y=None,
                 transform=None,
                 pre_transform=None,
                 smile_graph=None,
                 saliency_map=False):

        #root is required for save preprocessed data, default is '/tmp'
        super(TestbedDataset, self).__init__(root, transform, pre_transform)
        # benchmark dataset, default = 'davis'
        self.dataset = dataset
        self.saliency_map = saliency_map
        if os.path.isfile(self.processed_paths[0]):
            print('Pre-processed data found: {}, loading ...'.format(
                self.processed_paths[0]))
            self.data, self.slices = torch.load(self.processed_paths[0])
        else:
            print('Pre-processed data {} not found, doing pre-processing...'.format(
                self.processed_paths[0]))
            self.process(xd, xt, y, smile_graph)
            self.data, self.slices = torch.load(self.processed_paths[0])
        # dd = self.data
        # ss = self.slices
        # print(dd)
        # print(ss.keys())
        # print(dd.x.shape)
        # print(dd.c_size)
        print("PyTorch Dataset initialized.\n")

    @property
    def raw_file_names(self):
        pass
        #return ['some_file_1', 'some_file_2', ...]

    @property
    def processed_file_names(self):
        return [self.dataset + '.pt']

    def download(self):
        # Download to `self.raw_dir`.
        pass

    def _download(self):
        pass

    def _process(self):
        if not os.path.exists(self.processed_dir):
            os.makedirs(self.processed_dir)

    # Customize the process method to fit the task of drug-target affinity prediction
    # Inputs:
    # XD - list of SMILES, XT: list of encoded target (categorical or one-hot),
    # Y: list of labels (i.e. affinity)
    # Return: PyTorch-Geometric format processed data
    def process(self, xd, xt, y, smile_graph):
        assert (len(xd) == len(xt)
                and len(xt) == len(y)), "The three lists must be the same length!"
        data_list = []
        data_len = len(xd)
        for i in range(data_len):
            #print('Converting SMILES to graph: {}/{}'.format(i + 1, data_len))
            smiles = xd[i]  # SMILES of a drug
            target = xt[i]  # omic vector of cell
            labels = y[i]   # response
            # convert SMILES to molecular representation using rdkit
            c_size, features, edge_index = smile_graph[smiles]
            # make the graph ready for PyTorch Geometrics GCN algorithms:
            GCNData = DATA.Data(
                x=torch.Tensor(features),
                edge_index=torch.LongTensor(edge_index).transpose(1, 0),
                y=torch.FloatTensor([labels]))

            # require_grad of cell-line for saliency map
            if self.saliency_map == True:
                GCNData.target = torch.tensor([target],
                                              dtype=torch.float,
                                              requires_grad=True)
            else:
                GCNData.target = torch.FloatTensor([target])

            GCNData.__setitem__('c_size', torch.LongTensor([c_size]))
            # append graph, label and target sequence to data list
            data_list.append(GCNData)

        if self.pre_filter is not None:
            data_list = [data for data in data_list if self.pre_filter(data)]

        if self.pre_transform is not None:
            data_list = [self.pre_transform(data) for data in data_list]
        print('Graph construction done. Saving to file.')
        data, slices = self.collate(data_list)
        # save preprocessed data:
        torch.save((data, slices), self.processed_paths[0])

    def getXD(self):
        return self.xd

