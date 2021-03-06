#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""Test for multihead atteniton."""

import importlib
import pytest
import torch


def make_args(**kwargs):
    args = dict(
        kdim=32,
        qdim=32,
        adim=16,
        atype='scaled_dot',
        n_heads=4,
        dropout=0.1,
        dropout_head=0.,
        bias=True,
        param_init='xavier_uniform'
    )
    args.update(kwargs)
    return args


@pytest.mark.parametrize(
    "args", [
        ({'n_heads': 1}),
        ({'n_heads': 1, 'atype': 'add'}),
        ({'n_heads': 4}),
        ({'n_heads': 4, 'atype': 'add'}),
        ({'dropout_head': 0.5}),
        ({'bias': False}),
    ]
)
def test_forward(args):
    args = make_args(**args)

    batch_size = 4
    klen = 40
    qlen = 5
    key = torch.FloatTensor(batch_size, klen, args['kdim'])
    value = torch.FloatTensor(batch_size, klen, args['kdim'])
    query = torch.FloatTensor(batch_size, qlen, args['qdim'])
    src_mask = torch.ones(batch_size, 1, klen).byte()

    module = importlib.import_module('neural_sp.models.modules.multihead_attention')
    attention = module.MultiheadAttentionMechanism(**args)
    attention.train()
    aws = None
    for i in range(qlen):
        out = attention(key, value, query[:, i:i + 1], mask=src_mask, aw_prev=aws,
                        mode='parallel', cache=True)
        assert len(out) == 3
        cv, aws, _ = out
        assert cv.size() == (batch_size, 1, value.size(2))
        assert aws.size() == (batch_size, args['n_heads'], 1, klen)
