import tensorflow as tf
from tqdm import tqdm


def _parse_data_function(example):
    # 设置的梅尔倒谱的shape相乘的值
    data_feature_description = {
        'data': tf.io.FixedLenFeature([2880], tf.float32),
        'label': tf.io.FixedLenFeature([10], tf.int64),
    }
    return tf.io.parse_single_example(example, data_feature_description)


def train_reader_tfrecord(data_path, num_epochs, batch_size):
    raw_dataset = tf.data.TFRecordDataset(data_path)
    train_dataset = raw_dataset.map(_parse_data_function)
    # 依次为打乱 重复 取集
    train_dataset = train_dataset.shuffle(buffer_size=1000) \
        .repeat(count=num_epochs) \
        .batch(batch_size=batch_size) \
        .prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
    return train_dataset


def test_reader_tfrecord(data_path, batch_size):
    raw_dataset = tf.data.TFRecordDataset(data_path)
    test_dataset = raw_dataset.map(_parse_data_function)
    test_dataset = test_dataset.batch(batch_size=batch_size)
    return test_dataset


def get_train_data(data_path):
    train_dataset = train_reader_tfrecord(data_path, 1000, 50)
    batch_id = []
    data = []
    label = []
    for batch_temp, dataset_temp in tqdm(enumerate(train_dataset)):
        data_temp = dataset_temp["data"].numpy()
        data_temp = data_temp.reshape(50, 2880)        # 50个样本为一组，每个样本有80*36个信号数据
        label_temp = dataset_temp["label"].numpy()
        label_temp = label_temp.reshape(50, 10)
        batch_id.append(batch_temp)
        data.append(data_temp)
        label.append(label_temp)
    return batch_id, data, label
