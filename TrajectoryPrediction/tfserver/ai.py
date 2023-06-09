# import glob
# import matplotlib.pyplot as plt
# import matplotlib.cm as cm
from warnings import catch_warnings
import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras.layers import Dense, LSTM, Dropout, Reshape, Masking
from keras.models import Sequential, load_model
from control_params import params as cp
import datetime
import os.path

tf.compat.v1.enable_eager_execution()

class AI:
    def __init__(self, robot_id, filename) -> None:
        self.robot_id = robot_id
        self.filename = filename
        self.model = self.create_model()
        self.myHistory = None
        self.epoch = 0
        
    def create_model(self):
        model = Sequential()
        # model.add(Masking(mask_value=-10.,input_shape=cp['sample_shape']))
        model.add(LSTM(cp['EMBEDDING_SIZE'], input_shape=cp['sample_shape']))
        model.add(Dropout(cp['DROPOUT']))
        model.add(Dense(cp['FUTURE_TARGET']*cp['NUM_OUTPUTS']))
        model.add(Reshape([cp['FUTURE_TARGET'],cp['NUM_OUTPUTS']]))

        return model
    
    def recreate_model(self):
        self.model = self.create_model()

        # if os.path.isfile(file):
        #     self.model = load_model(file)
        # else:
        #     self.model.save(file) # should be called only once, when the model needs to be set for the first time*
    def save_model(self, file):
        self.model.save(file)
        
    def create_series_examples_from_batch(self, dataset, start_index, end_index, past_history, future_target):
        data = []
        labels = []
        list_dataset = list(dataset.values())
        array_dataset = np.asarray(list_dataset)
        for i in range(start_index, end_index):
            data.append(array_dataset[i][:past_history])
            labels.append(array_dataset[i][past_history:past_history+future_target])
        data = np.asarray(data).reshape(end_index-start_index, past_history, 2)
        labels = np.asarray(labels).reshape(end_index-start_index, future_target , 2)
        
        return data, labels

    def create_training_and_val_batch(self, batch, past_history=cp['PAST_HISTORY'], future_target=cp['FUTURE_TARGET'], input_dimension=cp['DIM_INPUT'], train_ratio = cp['TRAIN_RATIO']):
        x_train = np.zeros((1, past_history, input_dimension))
        y_train = np.zeros((1, future_target, input_dimension))
        x_val = np.zeros((1, past_history, input_dimension))
        y_val = np.zeros((1, future_target, input_dimension))

        for v in batch.values():
            tot_samples = len(v)
            print("total number of samples:", tot_samples)
            train_split = round(train_ratio * tot_samples)
            print("training samples:", train_split)
            x_train_tmp, y_train_tmp = self.create_series_examples_from_batch(v, 0, train_split, past_history, future_target)
            x_val_tmp, y_val_tmp = self.create_series_examples_from_batch(v, train_split, tot_samples, past_history,future_target)
            x_train = np.concatenate([x_train, x_train_tmp], axis=0)
            y_train = np.concatenate([y_train, y_train_tmp], axis=0)
            x_val = np.concatenate([x_val, x_val_tmp], axis=0)
            y_val = np.concatenate([y_val, y_val_tmp], axis=0)

        return x_train, x_val, y_train, y_val

    def train_model(self, train_set, val_set, train_step, val_step):
        self.myHistory = MyHistory()
        self.model.compile(optimizer='SGD', loss='mean_squared_error')
        self.model.fit(train_set, 
                       epochs=cp['LOCAL_EPOCHS'],
                       steps_per_epoch=train_step,
                       validation_data=val_set, 
                       validation_steps=val_step,
                       callbacks=[self.myHistory])
        self.epoch+=1
        # self.model.save(f'model_{str(self.robot_id)}.h5')

    def create_datasets(self, x_train, x_val, y_train, y_val):
        train_set = tf.data.Dataset.from_tensor_slices((x_train, y_train))
        train_set = train_set.cache().batch(cp['LOCAL_BATCH']).repeat()
        val_set = tf.data.Dataset.from_tensor_slices((x_val, y_val))
        val_set = val_set.cache().batch(cp['LOCAL_BATCH']).repeat()
        return train_set, val_set

    def load_data(self, filenames):
        """filter data v3

        Returns:
            _type_: _description_
        """
        count = 0
        samples = {count: []}
        for filename in filenames:
            with open(filename, 'r') as f:
                next(f)
                for line in f:
                    data = line.split(',')
                    if len(data) == 5:
                        if not samples[count]:
                            previous_id = float(data[1])
                            previous_time = float(data[2]) - 1
                        else:
                            previous_id = current_id
                            previous_time = current_time

                        current_id = float(data[1])
                        current_time = float(data[2])

                        x1 = float(data[3])
                        x2 = float(data[4])
                        if current_time - previous_time == 1 and previous_id == current_id:
                            samples[count].append((x1, x2))
                            if len(samples[count]) == 100:
                                count+=1
                                samples[count] = []
                        else: 
                            samples[count] = [(x1, x2)]
                    else:
                        samples[count] = [] # if there is an issue (file that is being written at the same time it is read, errors may occure)

                if len(samples[len(samples.keys())-1]) != 100:
                    # delete last empty trajectory
                    samples[count] = []

        if len(samples[len(samples.keys())-1]) != 100:
                # delete last empty trajectory
                del samples[count]

        return {1: samples}
    
    def tf_weights_to_list(self):
        """
        converts the weights of a model in to a 1D list
        """
        my_list = []
        for layer in self.model.layers:
            for weight in layer.weights:
                if len(weight.get_shape()) == 2:
                    for elem in weight:
                        my_list.extend(elem.numpy().tolist())
                elif len(weight.get_shape()) == 1:
                    my_list.extend(weight.numpy().tolist())
                else:
                    print("error, there is a shape of weigths that was not expected")
        return my_list
    
    def get_model_shape(self):
        """
        Returns a list which contains for each layer it's shape. 
        The shape is a tuple containing either 1 or 2 elem.
        """
        my_list = []
        for layer in self.model.layers:
            my_list.extend(tuple(weight.get_shape()) for weight in layer.weights)
        return my_list
    
    def reshape_list(self, shapes, weights):
        """
        Reshapes the list in the number of list that should be set. (This function is hard coded for the current model,
        meaning it won't work if the model changes...)

        Args:
            shapes (list): the shape of each layer of the model (use get_model_shape to get the according shape)
            weights (list): weights of the model in a 1D list format (use tf_weights _to_list to see an example)

        Returns:
            list: the weights rearanged to fit into the tensorflow model
        """
        i=0
        new_list = []
        for elem in shapes:
            if len(elem) == 1:
                new_list.append(np.array(weights[i:i+elem[0]]))
                i += elem[0]
            elif len(elem) == 2:
                temp = []
                for _ in range(elem[0]):
                    temp.append(weights[i:i+elem[1]])
                    i += elem[1]
                new_list.append(np.array(temp))
        first = new_list[:3]
        second = new_list[3:]
        return [first, second]
    
    def set_tf_weights(self, list_of_weights):
        """Sets the weights (list_of_weights) to the current model. The weights are a 1D list (same as the output of 
        tf_weight_to_list)

        Args:
            list_of_weights (list): 1D list of the weights you want to assign to the model.

        """
        shapes = self.get_model_shape()
        reshaped = self.reshape_list(shapes, list_of_weights)
        i = 0
        for layer in self.model.layers:
            for _ in layer.weights:
                layer.set_weights(reshaped[i])
                i += 1
                break

    def get_history(self):
        'return epoch,loss,val_loss,time'
        try:
            loss = self.myHistory.history['loss'][0] # maybe should be changed with -1
            val_loss = self.myHistory.history['val_loss'][0]
            time = self.myHistory.times[0]
            print(f"{self.epoch},{loss},{val_loss},{time}")
            return self.epoch, loss, val_loss, time
        except Exception:
            print("Error in the initialisation of myHistory variable.")
            return f"{self.epoch},error,error,error"
    
    def set_robot_id(self, robotID):
        self.robot_id = robotID

    def set_filename(self, filename):
        self.filename = f"../logs/{filename}"

    def get_model(self):
        return self.model

class MyHistory(tf.keras.callbacks.Callback):
    """Adapted from https://github.com/keras-team/keras/blob/master/keras/callbacks/callbacks.py#L614"""

    def on_train_begin(self, logs=None):
        self.epoch = []
        self.times = []
        self.history = {}
        self.start = datetime.datetime.now()

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        self.epoch.append(epoch)
        delta = float((datetime.datetime.now() - self.start).total_seconds())
        self.times.append(delta)
        for k, v in logs.items():
            self.history.setdefault(k, []).append(v)