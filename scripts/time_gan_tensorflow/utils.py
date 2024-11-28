import numpy as np
import pdb


def time_series_to_sequences(time_series, timesteps):
    '''
    Reshape the time series as sequences.
    '''
    # sequences = np.array([time_series[t - timesteps: t,:] for t in range(timesteps, len(time_series) + timesteps, timesteps)])
    sequences = [] 
    counter = 0 
    for t in range(timesteps, len(time_series) + timesteps, timesteps):
        tmp = time_series[t - timesteps: t]
        sequences.append(tmp)
        counter += 1 
        if counter >= time_series.shape[0]//timesteps:
            break 
    sequences =  np.array(sequences)
    return sequences


def sequences_to_time_series(sequences):
    '''
    Reshape the sequences as time series.
    '''
    time_series = np.concatenate([sequence for sequence in sequences], axis=0)
    return time_series

