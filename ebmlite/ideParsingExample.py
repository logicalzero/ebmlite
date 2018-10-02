import array

import core

try:
    import matplotlib.pyplot as plt
except Exception as E:
    print('To run this example, please install matplotlib')

# Load the IDE file.
schemaFile = './schemata/mide.xml'
ebmlFile = './tests/SSX46714-doesNot.ide'
schema = core.loadSchema(schemaFile)
ideRoot = schema.load(ebmlFile).dump()

# List the channels in the IDE file.
recProps = ideRoot['RecordingProperties']
chList = recProps['ChannelList']

# Print the ID and name of each channel.
print('Channels: %s'
      % str([[ch['ChannelID'], ch['ChannelName']] for ch in chList['Channel']]))

# Define the channel that we'll be working with.
chId = 8

# Get the channel that we want to work with from the list of channels.
chEl = [ch for ch in chList['Channel'] if ch['ChannelID'] == chId][0]

# Print the ID and name of each subchannel.
print('Subchannels: %s'
      % str([[sch['SubChannelID'], sch['SubChannelName']] for sch in chEl['SubChannel']]))

# Define the subchannel that we'll be working with.
schId = 0

# Get the channel that we want to work with from the list of channels.
schEl = [sch for sch in chEl['SubChannel'] if sch['SubChannelID'] == schId][0]

# Collect all the channelDataBlocks into a list.
dataBlocks = ideRoot['ChannelDataBlock']

# Filter the dataBlocks to only include blocks for the channel we want.
dataBlocks = [block for block in dataBlocks if block['ChannelIDRef'] == chId]

# Get the raw data from each ChannelDataBlock, and convert to an array.
rawData = ''
for block in dataBlocks:
    rawData += block['ChannelDataPayload']
rawArray = array.array(chEl['ChannelFormat'][1])
rawArray.fromstring(str(rawData))
xArray = array.array(chEl['ChannelFormat'][1])
[xArray.append(rawArray[i]) for i in range(0, len(rawArray), 3)]

# Calculate the time stamps of the data.
times = [x/5000.0 for x in range(len(xArray))]

# Plot the raw data from the IDE file.
plt.figure(1)
h = plt.plot(times, xArray)
plt.title('Raw Data')
plt.show()

# Make a list of polynomial IDs that affect ch8.0.
chCalId = chEl['ChannelCalibrationIDRef']
schCalId = chEl['SubChannel'][schId]['SubChannelCalibrationIDRef']

# Create a list of polynomials.
polys  = ideRoot['CalibrationList']['UnivariatePolynomial']
polys += ideRoot['CalibrationList']['BivariatePolynomial']

# filter the polynomials to whichever affect ch8.0
polys = [poly for poly in polys if poly['CalID'] in [chCalId, schCalId]]

# Apply calibration polynomials to the data, channel first, then subchannel.
# The subchannel polynomial is a bivariate polynomial, which references a
# different channel; however, the coefficients simplifies to f(x,y) = x, so we
# completely ignore it.
chPoly = polys[0]['PolynomialCoef']
calData = array.array('d')
[calData.append(x*chPoly[0] + chPoly[1]) for x in xArray]

# Plot the calibrated data.
plt.figure(2)
plt.plot(times, calData)
plt.title('Calibrated Data')
plt.show()