#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test for Transformer encoders."""

import importlib
import numpy as np
import pytest
import torch

from neural_sp.models.torch_utils import np2tensor
from neural_sp.models.torch_utils import pad_list


def make_args(**kwargs):
    args = dict(
        input_dim=80,
        enc_type='transformer',
        attn_type='scaled_dot',
        n_heads=4,
        n_layers=6,
        n_layers_sub1=0,
        n_layers_sub2=0,
        d_model=64,
        d_ff=256,
        last_proj_dim=0,
        pe_type='none',
        layer_norm_eps=1e-12,
        ffn_activation='relu',
        dropout_in=0.1,
        dropout=0.1,
        dropout_att=0.1,
        dropout_layer=0.1,
        n_stacks=1,
        n_splices=1,
        conv_in_channel=1,
        conv_channels="32_32",
        conv_kernel_sizes="(3,3)_(3,3)",
        conv_strides="(1,1)_(1,1)",
        conv_poolings="(2,2)_(2,2)",
        conv_batch_norm=False,
        conv_layer_norm=False,
        conv_bottleneck_dim=0,
        conv_param_init=0.1,
        task_specific_layer=False,
        param_init='xavier_uniform',
        chunk_size_left=-1,
        chunk_size_current=-1,
        chunk_size_right=-1
    )
    args.update(kwargs)
    return args


@pytest.mark.parametrize(
    "args", [
        # Transformer type
        ({'enc_type': 'transformer'}),
        ({'enc_type': 'conv_transformer'}),
        ({'enc_type': 'conv_transformer', 'input_dim': 240, 'conv_in_channel': 3}),
        # positional encoding
        ({'pe_type': 'add'}),
        # normalization
        ({'enc_type': 'conv_transformer', 'conv_batch_norm': True}),
        ({'enc_type': 'conv_transformer', 'conv_layer_norm': True}),
        # projection
        ({'enc_type': 'conv_transformer', 'last_proj_dim': 256}),
        # LC-Transformer
        ({'enc_type': 'transformer', 'chunk_size_left': 96, 'chunk_size_current': 64, 'chunk_size_right': 32}),
        # Multi-task
        ({'enc_type': 'transformer', 'n_layers_sub1': 4}),
        ({'enc_type': 'transformer', 'n_layers_sub1': 4, 'task_specific_layer': True}),
        ({'enc_type': 'transformer', 'n_layers_sub1': 4, 'n_layers_sub2': 3}),
        ({'enc_type': 'transformer', 'n_layers_sub1': 4, 'n_layers_sub2': 3, 'task_specific_layer': True}),
    ]
)
def test_forward(args):
    args = make_args(**args)

    batch_size = 4
    xmaxs = [40, 45] if args['chunk_size_left'] == -1 else [1600, 1655]
    device_id = -1
    module = importlib.import_module('neural_sp.models.seq2seq.encoders.transformer')
    enc = module.TransformerEncoder(**args)
    for xmax in xmaxs:
        xs = np.random.randn(batch_size, xmax, args['input_dim']).astype(np.float32)
        xlens = torch.IntTensor([len(x) for x in xs])
        xs = pad_list([np2tensor(x, device_id).float() for x in xs], 0.)
        enc_out_dict = enc(xs, xlens, task='all')

        assert enc_out_dict['ys']['xs'].size(0) == batch_size
        assert enc_out_dict['ys']['xs'].size(1) == enc_out_dict['ys']['xlens'][0]
        if args['n_layers_sub1'] > 0:
            assert enc_out_dict['ys_sub1']['xs'].size(0) == batch_size
            assert enc_out_dict['ys_sub1']['xs'].size(1) == enc_out_dict['ys_sub1']['xlens'][0]
        if args['n_layers_sub2'] > 0:
            assert enc_out_dict['ys_sub2']['xs'].size(0) == batch_size
            assert enc_out_dict['ys_sub2']['xs'].size(1) == enc_out_dict['ys_sub2']['xlens'][0]
