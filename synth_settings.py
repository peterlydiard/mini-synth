# load modules
import csv

def read_synth_data(filename):

    # first and second column data arrays (strings)
    names = []
    values = []

    try:
        # open file for reading
        with open(filename) as csv_data_file:

            # open file as csv file
            csv_reader = csv.reader(csv_data_file)

            # loop over rows
            for row in csv_reader:

                # add cell [0] to list of names
                names.append(row[0])

                # add cell [1] to list of values
                values.append(row[1])
                
            print("synth_data.py: Data read from file: " + filename)

    except:
        print("synth_data.py: WARNING: file: \'" + filename + "\' not found, or wrong format.")
        
    return names, values

# Write user names and settings to the given file.
# A new file will be created or an old file will be overwritten.
def write_synth_data(filename, names, values):
    
    with open(filename, "w", newline='') as csv_data_file:
        
        csv_writer = csv.writer(csv_data_file, delimiter=',')
        
        # print(names, values)
        
        for i in range(len(names)):
            csv_writer.writerow([names[i], values[i]])
            
    print("synth_data.py: Data written to file: " + filename)

#------------------------Module tests-----------------------
#if __name__ == "__main__":
def test_synth_data(filename):
    # read old settings
    names, values = read_synth_data(filename)
    
    names.append("Mode")
    values.append(5)
    
    write_synth_data(filename, names, values)

    # print(names, values)

