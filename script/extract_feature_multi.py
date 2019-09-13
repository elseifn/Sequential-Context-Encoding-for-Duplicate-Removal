import sys
import os.path as osp
sys.path.append(osp.abspath(osp.join(__file__, '../../')))
from evaluation import COCO
from evaluation import COCOeval
from models.rnn_model_full_global_attention_context_gate import Encoder_Decoder
# from models.rnn_model_full_global_attention_context_gate_mullayer_inmul_mulhead import Encoder_Decoder
# from dataset.multi_dataset_before_before_nms import TrainDataset
# from dataset.multi_dataset_after_nms_weight_v2 import TrainDataset
# from dataset.multi_dataset_after_nms_weight_v3 import TrainDataset
from dataset.multi_dataset_before_before_no_gt_nms_testdev import TrainDataset, unique_collate
# from dataset.multi_dataset_full_nms import TrainDataset
from solver.extract_full_nms_multi import test_solver
# from solver.test_full_nms_multi_inmul import test_solver
import torch
import argparse
import os
from multiprocessing import Process, Manager
import cvbase as cvb

def parse_args():
    parser = argparse.ArgumentParser(description='Test RNN NMS')
    parser.add_argument('--hidden_size', 
    					default=128,
    					type=int,
    					help='the hidden size of RNN')

    parser.add_argument('--gt_path', 
                        default='/mnt/lustre/liushu1/qilu_ex/dataset/coco/annotations/instances_val2017.json',
                        help='the path of gt json')

    parser.add_argument('--base_path', 
    					default='/mnt/lustre/liushu1/qilu_ex/dataset/test_dev/panet/',
    					help='the data path of RNN')

    parser.add_argument('--img_list',
    					default='test.txt',
    					help='the img_list')

    parser.add_argument('--output_dir',
    					default='/mnt/lustre/liushu1/qilu_ex/RNN_NMS/panet_before_mlp_source_weight4/',
    					help='the save path of output_dir')

    parser.add_argument('--ann_type',
                        default='bbox',
                        help='the type of anns, det or segm')

    parser.add_argument('--thread_all', 
                        default=8,
                        type=int,
                        help='the hidden size of RNN')

    parser.add_argument('--attn_type',
                        default='mlp',
                        help='the attn_type')

    parser.add_argument('--context_type',
                        default='source',
                        help='the attn_type, source, target, both')
    
    parser.add_argument('--n_layers', 
                        default=1,
                        type=int,
                        help='the layers of RNN')

    parser.add_argument('--multi_head',
                        default=1,
                        type=int,
                        help='the number of multi_head')
    args = parser.parse_args()
    return args


def run(thread_index, thread_num, result, args):
    # initialization
    model_dir = os.path.join(args.output_dir, 'model/')
    model_path = os.path.join(model_dir, 'latest.pth')
    if not osp.exists(model_path):
        raise "there is no latest.pth "

    output_dir = [model_path, result_dir]
    use_cuda = torch.cuda.is_available()

    cls_list = ['_' for _ in range(81)]
    # datasets
    val = TrainDataset(args.base_path, args.img_list, 'msra', cls_list, phase='test')
    # val_loader = torch.utils.data.DataLoader(val, batch_size=1, num_workers=1, collate_fn=unique_collate, pin_memory=False)

    # model
    # model = Encoder_Decoder(args.hidden_size, attn_type=args.attn_type, context_type=args.context_type, n_layers=args.n_layers, multi_head=args.multi_head)
    model = Encoder_Decoder(args.hidden_size, attn_type=args.attn_type, context_type=args.context_type)

    if use_cuda:
        model = model.cuda()
    
    model.eval()
    thread_result = test_solver(model, val, output_dir, thread_index, thread_num)
    result.extend(thread_result)
    # print('thread_index:{}, index:{}, image_id:{}, cost:{}'.format(thread_index, count, image_id, print_time))

if __name__ == '__main__':
    with Manager() as manager:
        args = parse_args()
        result_dir = os.path.join(args.output_dir, 'result/')
        if not osp.exists(result_dir):
            os.makedirs(result_dir)
        result_path = os.path.join(result_dir, 'result.json')
        result = manager.list()
        
        p_list = []
        # for i in range(args.thread_all):
        # for i in range(0, 2):
        # for i in range(2, 4):
        # for i in range(4, 6):
        for i in range(6, 8):
            p = Process(target=run, args=(i, args.thread_all, result, args))
            p.start()
            p_list.append(p)

        for res in p_list:
            res.join()

        