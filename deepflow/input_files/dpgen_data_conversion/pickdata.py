import dpdata
import numpy as np

# load data of cp2k/aimd_output format
data = dpdata.LabeledSystem('data', fmt = 'cp2k/aimd_output', restart=True)


#print('# the data contains %d frames' % len(data))
print(data)
index_data = np.array(range(len(data)))
print('total data indexes',index_data, len(index_data))

# Specify additional ranges to include
#additional_ranges = [(10000, 20000),(48000,56000)]

# Extract elements from specified ranges
#additional_data = []
#for start, end in additional_ranges:
#    additional_data.extend(index_data[start:end+1])

# Create the training_index by combining every 4th element and the additional ranges
#training_index = index_data[::3] + list(set(additional_data) - set(index_data))
training_index = index_data[::3]


print('indexes for training', training_index, len(training_index))

# other indexes left after training_data
left_indexes = list(set(index_data)-set(training_index))
print("points left %d" % len(left_indexes))

#pick every randomly for validation point from the left indexes
val_number = int(0.15*(len(training_index)))
validation_index =  np.random.choice(training_index,size=val_number,replace=False)
#test_index = list(set(left_indexes)-set(validation_index))
print("indexes for validation", validation_index, len(validation_index))
print("indexes for testing", left_indexes, len(left_indexes))



#convert the picked data and validation data to deep md format

data_training = data.sub_system(training_index)
#data_left = data.sub_system(left_indexes)
data_validation = data.sub_system(validation_index)
data_testing = data.sub_system(left_indexes)
print('training',data_training)
#print('testing',data_left)
print('validation', data_validation)
print('testing', data_testing)
# all training data put into directory:"training_data"
data_training.to_deepmd_npy('training_data')
#data_left.to_deepmd_npy('testing')
# all validation data put into directory:"validation_data"
data_validation.to_deepmd_npy('validation_data')
data_testing.to_deepmd_npy('testing_data')
print('# the training data contains %d frames' % len(data_training))
print('# the validation data contains %d frames' % len(data_validation))
print('# the validation data contains %d frames' % len(data_testing))
