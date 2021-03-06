import os
import re
import argparse
from collections import defaultdict
import random
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import matplotlib.legend as lgd
import matplotlib.markers as mks
import pdb

class TrainLog(object):
    '''train log file analyze and data collection'''
    def __init__(self, log_files):
        '''init func'''
        self._log_files = log_files
        self._multi_losses = defaultdict(list)
        self._multi_lrs = defaultdict(list)
        self._multi_iterations = defaultdict(list)
        self._multi_mbox_losses = defaultdict(list)
        self._multi_test_iterations = defaultdict(list)
        self._multi_detection_accuracies = defaultdict(list)
        self._parse_log()
        self._is_detection = True if len(self._multi_mbox_losses) > 0 else False

    def _parse_log(self):
        '''parse log files to obtain loss and iteration data'''
        def obtain_log_name(log_file):
            '''get log name from log file'''
            if not os.path.isfile(log_file):
                raise Exception('Error: log file {} does not exist.'.format(self.log_file))
            #Might need to change this to have a better representation in the future, so keep it here
            return log_file
            
        def obtain_process_id(line):
            '''get process id from line string'''
            process_id_pattern = re.compile('\[\d+\]')
            process_id_list = process_id_pattern.findall(line)
            return '0' if len(process_id_list) == 0 else process_id_list[0][1:-1]

        loss_pattern = re.compile('.* Iteration \d+, loss = .*')
        lr_pattern = re.compile('.* Iteration \d+, lr = .*')
        mbox_loss_pattern = re.compile('.* Train net output #\d+: mbox_loss = .*')
        detection_accuracy_pattern = re.compile('.* Test net output #\d+: detection_eval = .*')
        test_iteration_pattern = re.compile('.* Iteration \d+, Testing net \(#\d+\).*')
        for log_file in self._log_files:
            log_name = obtain_log_name(log_file)
            with open(log_file, 'r') as f:
                for line in f.readlines():
                    if re.match(loss_pattern, line):
                        if '0' != obtain_process_id(line):
                            continue
                        self._multi_losses[log_name].append(float(line.split()[-1]))
                        self._multi_iterations[log_name].append(int(line.split()[-4][:-1]))
                    elif re.match(lr_pattern, line):
                        if '0' != obtain_process_id(line):
                            continue
                        self._multi_lrs[log_name].append(float(line.split()[-1]))
                    elif re.match(mbox_loss_pattern, line):
                        if '0' != obtain_process_id(line):
                            continue
                        self._multi_mbox_losses[log_name].append(float(line.split()[-2]))
                    elif re.match(test_iteration_pattern, line):
                        if '0' != obtain_process_id(line):
                            continue
                        self._multi_test_iterations[log_name].append(float(line.split()[-4][:-1]))
                    elif re.match(detection_accuracy_pattern, line):
                        if '0' != obtain_process_id(line):
                            continue
                        self._multi_detection_accuracies[log_name].append(float(line.split()[-1]))

    @property
    def is_detection(self):
        '''check if current train log is generated by detection or classification'''
        return self._is_detection

    @property
    def iterations(self):
        '''get iterations showed within log file'''
        return self._multi_iterations

    @property
    def test_iterations(self):
        '''get test iterations showed within log file'''
        return self._multi_test_iterations

    @property
    def losses(self):
        '''get losses data showed within log file'''
        return self._multi_losses

    @property
    def mbox_losses(self):
        '''get mbox losses data showed within log file'''
        return self._multi_mbox_losses

    @property
    def lrs(self):
        '''get lrs data showed within log file'''
        return self._multi_lrs

    @property
    def detection_accuracies(self):
        '''get detection accuracies data showed within log file'''
        return self._multi_detection_accuracies

class PlotTrend(object):
    '''plot single or multi trends within a fig'''
    def __init__(self, y_items, x_items, out_dir):
        '''init func'''
        self.y_items = y_items
        self.x_items = x_items
        self.y_axis_name = y_items.keys()[0]
        self.x_axis_name = x_items.keys()[0]
        self.y_dict = y_items.values()[0]
        self.x_dict = x_items.values()[0]
        self.out_dir = out_dir

    def get_chart_type_description(self):
        '''get chart type description'''
        y_field, x_field = self.y_axis_name, self.x_axis_name
        chart_type_desc_separator = ' vs. '
        return chart_type_desc_separator.join([y_field, x_field])

    def get_legend_loc(self):
        '''get legend loc'''
        loc = 'lower right'
        if self.y_axis_name.find('accuracy') != -1:
            loc = 'lower right'
        elif self.y_axis_name.find('loss') != -1 or self.y_axis_name.find('lr') != -1:
            loc = 'upper right'
        return loc

    def result_png_file(self, y_field):
        '''generate result png file based on y field name'''
        return self.out_dir + y_field + '_plot.png'

    def random_marker(self):
        '''return random marker for plot'''
        markers = mks.MarkerStyle.markers
        num = len(markers.values())
        idx = random.randint(0, num - 1)
        return markers.values()[idx]

    def get_data_label(self, log_name):
        '''get data source label'''
        label = log_name
        return label

    def plot(self):
        '''plot trends'''
        if len(self.y_dict) != len(self.x_dict):
            raise Exception("Error: y_dict and x_dict are not having equal size.")
        self.plot_multiple_trends(self.y_dict, self.x_dict)

    def plot_multiple_trends(self, y_dict, x_dict):
        '''plot y_items and x_items into a single fig'''
        for key in y_dict:
            y_list, x_list = y_dict[key], x_dict[key]
            # Within current log, number of iterations is 1 more than number of lrs
            if len(y_list) != len(x_list):
                if len(y_list) < len(x_list) and len(y_list) > 0:
                    x_list = x_list[:len(y_list)]
                else:
                    raise Exception('Error: y list has distinct length with x list')
            color = [random.random(), random.random(), random.random()]
            linewidth = 0.75
            label = self.get_data_label(key)
            plt.plot(x_list, y_list, label = label, color = color, 
                     linewidth = linewidth)
            legend_loc = self.get_legend_loc()
            plt.legend(loc = legend_loc, ncol = 1) # adjust ncol to fit the space
            plt.title(self.get_chart_type_description())
            plt.xlabel(self.x_axis_name)
            plt.ylabel(self.y_axis_name)
        png_file = self.result_png_file(self.y_axis_name)
        plt.savefig(png_file)
        plt.show()

def plot_loss_trends(train_log, out_dir):
    '''plot loss trends of train logs'''
    y_items = {'loss' : train_log.losses}
    x_items = {'Iterations' : train_log.iterations}
    #pdb.set_trace()
    plot_trend = PlotTrend(y_items, x_items, out_dir)
    plot_trend.plot()

def plot_mbox_loss_trends(train_log, out_dir):
    '''plot mbox loss trends of train logs'''
    if not train_log.is_detection: return
    y_items = {'mbox loss' : train_log.mbox_losses}
    x_items = {'Iterations' : train_log.iterations}
    plot_trend = PlotTrend(y_items, x_items, out_dir)
    plot_trend.plot()

def plot_lr_trends(train_log, out_dir):
    '''plot lrs trend of train logs'''
    y_items = {'lr' : train_log.lrs}
    x_items = {'Iterations' : train_log.iterations}
    plot_trend = PlotTrend(y_items, x_items, out_dir)
    plot_trend.plot()

def plot_detection_accuracy_trends(train_log, out_dir):
    '''plot detection accuracy trend of train logs'''
    if not train_log.is_detection: return
    y_items = {'detection accuracy' : train_log.detection_accuracies}
    x_items = {'Test iterations' : train_log.test_iterations}
    plot_trend = PlotTrend(y_items, x_items, out_dir)
    plot_trend.plot()

def parse_args():
    '''parse program arguments'''
    description = ('Parse Caffe training log and plot loss trends,\
                    Before running it, you need to install tkinter package,\
                    python plot_loss_trends.py -l/--log_files your/log/files \
                    [-o/--output_dir your/output/directory, default is your pwd directory]')
    parser = argparse.ArgumentParser(description = description)
    parser.add_argument('-l', '--log_files',
                        nargs = '+',
                        help = 'caffe training log file path')
    parser.add_argument('-o', '--output_dir',
                        default = './',
                        help = 'Directory in which to place output result files')
    args = parser.parse_args()
    return args

def main():
    '''main routine'''
    args = parse_args()
    print args
    train_log = TrainLog(args.log_files)
    plot_loss_trends(train_log, args.output_dir)
    plot_mbox_loss_trends(train_log, args.output_dir)
    plot_lr_trends(train_log, args.output_dir)
    plot_detection_accuracy_trends(train_log, args.output_dir)

if __name__ == '__main__':
    main()
