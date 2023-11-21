import numpy as np
import random

class RTLearner(object):

    def __init__(self, leaf_size=5, verbose=False):
        self.leaf_size = leaf_size
        self.model = []
        np.random.seed(903951120)

    def add_evidence(self, x, y):
        if len(x) <= self.leaf_size:
            return np.array([[-1, np.median(y), -1, -1]])
        elif len(set(y)) <= self.leaf_size:
            return np.array([[-1, np.median(y), -1, -1]])
        else:
            max_corr_index = int(random.randint(0, len(x[0])-1))
            split_val = np.median(x[:, max_corr_index])
            left_x = []
            left_y = []
            right_x = []
            right_y = []
            for i in range(len(x)):
                if x[i][max_corr_index] <= split_val:
                    if len(left_x) == 0:
                        left_x = np.array([x[i]])
                        left_y = np.array(y[i])
                    else:
                        left_x = np.vstack((left_x, x[i]))
                        left_y = np.append(left_y, y[i])
                else:
                    if len(right_x) == 0:
                        right_x = np.array([x[i]])
                        right_y = np.array(y[i])
                    else:
                        right_x = np.vstack((right_x, x[i]))
                        right_y = np.append(right_y, y[i])
            if len(right_x) == 0 or len(left_x) == 0:
                left_x = []
                left_y = []
                right_x = []
                right_y = []
                split_val -= 0.00000001
                for i in range(len(x)):
                    if x[i][max_corr_index] <= split_val:
                        if len(left_x) == 0:
                            left_x = np.array([x[i]])
                            left_y = np.array(y[i])
                        else:
                            left_x = np.vstack((left_x, x[i]))
                            left_y = np.append(left_y, y[i])
                    else:
                        if len(right_x) == 0:
                            right_x = np.array([x[i]])
                            right_y = np.array(y[i])
                        else:
                            right_x = np.vstack((right_x, x[i]))
                            right_y = np.append(right_y, y[i])
            if len(right_x) == 0 or len(left_x) == 0:
                return np.array([[-1, np.median(y), -1, -1]])
            left_tree = self.add_evidence(left_x, left_y)
            right_tree = self.add_evidence(right_x, right_y)
            for i in range(len(left_tree)):
                if not left_tree[i][0] == -1:
                    left_tree[i][2] += 1
                    left_tree[i][3] += 1
            for i in range(len(right_tree)):
                if not right_tree[i][0] == -1:
                    right_tree[i][2] += 1+left_tree.shape[0]
                    right_tree[i][3] += 1+left_tree.shape[0]
            root = np.array([max_corr_index, split_val, 1, left_tree.shape[0]+1])
            first_array = np.vstack((root, left_tree))
            self.model = np.vstack((first_array, right_tree))
            return np.vstack((first_array, right_tree))

    def query(self, points):
        result_array = []
        for point in points:
            node = int(0)
            while not self.model[node][-1] == -1:
                if point[int(self.model[node][0])] <= self.model[node][1]:
                    node = int(self.model[node][2])
                else:
                    node = int(self.model[node][3])
            if len(result_array) == 0:
                result_array = np.array([self.model[int(node)][1]])
            else:
                result_array = np.append(result_array, self.model[int(node)][1])
        return result_array
