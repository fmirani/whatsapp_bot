#!/usr/bin/env python3

import fire
import json
import os
import numpy as np
import tensorflow as tf

import model, sample, encoder

def interact_model(
    message,
    model_name='fm_model',
    seed=5,
    nsamples=1,
    batch_size=1,
    length=100,
    temperature=0.5,
    top_k=20,
    top_p=0.9,
):
    if batch_size is None:
        batch_size = 1
    assert nsamples % batch_size == 0

    enc = encoder.get_encoder(model_name)
    hparams = model.default_hparams()
    with open(os.path.join('models',
                           model_name,
                           'hparams.json')) as f:
        hparams.override_from_dict(json.load(f))

    if length is None:
        length = hparams.n_ctx // 2
    elif length > hparams.n_ctx:
        raise ValueError("Can't get samples longer"
                         " than window size: %s" % hparams.n_ctx)

    with tf.Session(graph=tf.Graph()) as sess:
        context = tf.placeholder(tf.int32, [batch_size, None])
        np.random.seed(seed)
        tf.set_random_seed(seed)
        output = sample.sample_sequence(
            hparams=hparams, length=length,
            context=context,
            batch_size=batch_size,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )

        saver = tf.train.Saver()
        ckpt = tf.train.latest_checkpoint(os.path.join('models',
                                                       model_name))
        saver.restore(sess, ckpt)

        if message == "":
            return -1
        raw_text = message

        context_tokens = enc.encode(raw_text)
        out = sess.run(output, feed_dict={
            context: [context_tokens for _ in range(batch_size)]
        })[:, len(context_tokens):]
        text = []
        for i in range(batch_size):
            text.append(enc.decode(out[i]))

        return text


if __name__ == '__main__':
    print(fire.Fire(interact_model))