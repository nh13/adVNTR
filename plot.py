
def plot1():
    stat_files = ['0_size_related_reads.txt', '1_size_sensitivity.txt', '2_size_blast_selected.txt',
                  '3_sim_read_coverage__gc_content.txt']

    x_label = {0: 'Pattern Size', 1: 'Pattern Size', 2: 'Pattern Size', 3: 'Simulated Read Coverage'}
    y_label = {0: 'Reads from the pattern', 1: 'Sensitivity', 2: 'Number of Selected Reads by Blast', 3: 'GC Content'}


    i = 0
    for file_name in stat_files:
        import matplotlib.pyplot as plt

        X = []
        Y = []
        with open(file_name) as input_file:
            lines = input_file.readlines()
            for line in lines:
                line = line.strip()
                if line == '':
                    continue
                nums = [float(n) for n in line.split()]
                X.append(nums[0])
                Y.append(nums[1])
        plt.plot(X, Y, 'o')
        plt.xlabel(x_label[i])
        plt.ylabel(y_label[i])
        plt.savefig('%s.png' % file_name)   # save the figure to file
        plt.close()
        i += 1

def plot2():
    dirs = ['original_case_r1_p1/', 'penalty_3_reward_1/']
    stat_files = ['1_size_sensitivity.txt', '2_size_blast_selected.txt']

    x_label = {1: 'Pattern Size', 2: 'Pattern Size'}
    y_label = {1: 'Sensitivity', 2: 'Number of Selected Reads by Blast'}

    X = []
    Y = [[], []]
    diagram_index = 1
    for file_name in stat_files:
        import matplotlib.pyplot as plt
        for i in range(len(dirs)):
            with open(dirs[i] + file_name) as input_file:
                lines = input_file.readlines()
                for line in lines:
                    line = line.strip()
                    if line == '':
                        continue
                    nums = [float(n) for n in line.split()]
                    if i == 0:
                        X.append(nums[0])
                    Y[i].append(nums[1])
        plt.plot(X, Y[0], 'o', label='same penalty and reward')
        plt.plot(X, Y[1], 'o', label='penalty = 3 * reward')
        plt.xlabel(x_label[diagram_index])
        plt.ylabel(y_label[diagram_index])
        plt.legend(loc=0)
        plt.savefig('compare_%s.png' % file_name)   # save the figure to file
        plt.close()
        diagram_index += 1


def plot_coverage_comparison():
    stat_files = ['10X_ratio.txt', '20X_ratio.txt', '30X_ratio.txt']
    coverages = [10, 20, 30]
    X = [[], [], []]
    Y = [[], [], []]

    import matplotlib.pyplot as plt

    for i in range(len(stat_files)):
        with open(stat_files[i]) as input_file:
            lines = input_file.readlines()
            for line in lines:
                line = line.strip()
                if line == '':
                    continue
                nums = [float(n) for n in line.split()]
                X[i].append(coverages[i])
                Y[i].append(nums[1])
    plt.plot(X[0], Y[0], 'o', label='10X')
    plt.plot(X[1], Y[1], 'o', label='20X')
    plt.plot(X[2], Y[2], 'o', label='30X')
    averages = []
    for i in range(3):
        sum = 0
        for e in Y[i]:
            sum += e
        averages.append(float(sum) / len(Y[i]))
    plt.plot(coverages, averages, label='avg')
    plt.xlabel('Coverage')
    plt.ylabel('Copy Count / True Copy Count')
    plt.legend(loc=0)
    plt.savefig('compare_%s.png' % 'coverages')  # save the figure to file
    plt.close()


def plot_cn_over_sens():
    stat_file = '20X_ratio.txt'
    stat_file2 = '20X_ratio_at_least_two_copy.txt'
    sens_file = 'original_case_r1_p1/1_size_sensitivity.txt'
    X = []
    Y = []
    Y2 = []

    import matplotlib.pyplot as plt

    with open(stat_file) as input_file:
        lines = input_file.readlines()
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            nums = [float(n) for n in line.split()]
            Y.append(nums[1])
    with open(stat_file2) as input_file:
        lines = input_file.readlines()
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            nums = [float(n) for n in line.split()]
            Y2.append(nums[1])

    with open(sens_file) as input_file:
        lines = input_file.readlines()
    for line in lines:
        line = line.strip()
        if line == '':
            continue
        nums = [float(n) for n in line.split()]
        X.append(nums[1])
    plt.plot(X, Y2, 'o', color='blue', label='Filtered reads with at least two copy')
    plt.plot(X, Y, 'o', color='red', label='All reads')
    plt.xlabel('Sensitivity')
    plt.ylabel('Copy Count / True Copy Count')
    plt.legend(loc=0)
    plt.savefig('CN_over_sens_compare.png')  # save the figure to file
    plt.close()


def plot_tandem_copy_number_and_genome_copy_number():
    stat_file = 'copy_number_analysis.txt'
    sens_file = 'original_case_r1_p1/1_size_sensitivity.txt'
    X = []
    Y = []
    Y2 = []

    import matplotlib.pyplot as plt

    with open(stat_file) as input_file:
        lines = input_file.readlines()
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            nums = [float(n) for n in line.split()]
            Y.append(float(nums[1]) / nums[0])

    with open(sens_file) as input_file:
        lines = input_file.readlines()
    for i in range(len(lines)):
        line = lines[i]
        line = line.strip()
        if line == '':
            continue
        nums = [float(n) for n in line.split()]
        X.append(nums[0])
    plt.plot(X, Y, 'o', color='blue', label='CN in 100Kbp region / CN in ~1Kbp region')
    # plt.plot(X, Y2, 'o', color='red', label='CN in 100Kbp region')
    plt.xlabel('Pattern size')
    plt.ylabel('Copies 100k / Copies in 1K')
    plt.legend(loc=0)
    plt.savefig('CN_in_genome_compare.png')  # save the figure to file
    plt.close()

# plot_cn_over_sens()
plot_tandem_copy_number_and_genome_copy_number()