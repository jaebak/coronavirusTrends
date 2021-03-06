#!/usr/bin/env python
try:
  import urllib2
except:
  import urllib.request as urllib2
import csv
import array
import collections
import re
import os
import glob
import datetime
import argparse
import matplotlib.pyplot as plt
import numpy as np

def drawCases(data, interestedIndex=3, title="Total Cases", filename='totalCases.pdf', dayLimit=-1, lowLimitCase=200, maxCase = -1, interestedCountries=[], ignoreCountries=['Worldwide', 'International conveyance (Diamond Princess)', 'International', 'Others', 'World', 'Cruise Ship'], maxExcludeCountry = ['China']):
  # Collect interested data depending on rowIndex. Sort country by number of cases
  # data[country][date] = (newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases)
  # interestData[country][date] = case
  interestData = collections.OrderedDict()
  for country in sorted(data, key=lambda c: list(data[c].values())[-1][4], reverse=True):
    # Ignore countries
    if country in ignoreCountries: continue
    # Select interested countries
    if len(interestedCountries) != 0:
      if country not in interestedCountries: continue
    # Append interest data
    for date in data[country]:
      # Parse case
      case = data[country][date][interestedIndex]
      if case == None: continue
      case = int(case)
      # Append case
      if country not in interestData: interestData[country] = collections.OrderedDict()
      interestData[country][date] = case

  # Convert to plt format
  # interestDataPlt[country] = ([iDay],[case])
  interestDataPlt = collections.OrderedDict()
  for country in interestData:
    for iDate, date in enumerate(interestData[country]):
      if country not in interestDataPlt: interestDataPlt[country] = [array.array('d'), array.array('d')]
      interestDataPlt[country][0].append(iDate)
      interestDataPlt[country][1].append(interestData[country][date])

  markers = ['o','v','^','<','>','s','p','*','H','D']
  colors = ['k', 'blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'grey', 'olive', 'cyan']

  plt.figure(figsize=(7.5,7.5))
  plt.rcParams['legend.numpoints'] = 1
  maxEntry = 0
  minEntry = 0
  maxDays = 0
  for iCountry, country in enumerate(interestDataPlt):
    xArray = array.array('d')
    yArray = array.array('d')
    nPoints = len(interestDataPlt[country][0])
    passIncreasePoint = lowLimitCase
    hasPassed = False
    countPoints = 0
    for iPoint in range(nPoints):
      if iPoint != nPoints-1 : 
        increase = interestDataPlt[country][1][iPoint+1]-interestDataPlt[country][1][iPoint]
        if increase > passIncreasePoint:
          hasPassed = True
      # Has passed increase threshold
      if hasPassed:
        # Append data
        xArray.append(countPoints)
        yArray.append(interestDataPlt[country][1][iPoint])
        # Find y max and x max
        if country not in maxExcludeCountry:
          # Limit number of days
          if dayLimit == -1 or countPoints < dayLimit:
            minEntry = min([minEntry, min(yArray)])
            maxEntry = max([maxEntry, max(yArray)])
            maxDays = max([maxDays, max(xArray)])
        countPoints += 1
    # If there is data passing increase threshold plot graph
    if countPoints!= 0:
      line, = plt.plot(xArray, yArray, color=colors[iCountry%len(colors)], linestyle='solid', marker=markers[iCountry%len(markers)], label=country, markersize=10)
      plt.legend(loc="upper left", fontsize=10)
   
  # Graph settings
  axes = plt.gca()
  axes.set_xlim([0,maxDays+1])
  axes.set_xlabel("Number of days from a daily increase of "+str(lowLimitCase)+" cases", fontsize=15)
  axes.set_xticks(np.arange(0,maxDays+1, step=1))
  axes.set_ylim([minEntry, maxEntry*1.2])
  axes.set_ylabel('Cases', fontsize=15)
  axes.set_title(title, fontsize=30, y=1.04)

  print('Saving '+filename)
  plt.savefig(filename)

def getDataFromWorldInData(dataFolder='./', tag=''):
  if not os.path.exists(dataFolder): os.makesdir(dataFolder)
  confirmedUrl = 'http://cowid.netlify.com/data/full_data.csv'
  filepath = os.path.join(dataFolder, tag+os.path.basename(confirmedUrl))

  # Gets data from url
  inFile = urllib2.urlopen(confirmedUrl)
  # Saves data
  tempData = inFile.read().decode('utf-8')
  print('Saving '+confirmedUrl+' to '+filepath)
  with open(filepath,'w') as outFile:
    outFile.write(tempData)

  # Collect rawData from file
  # inFile[0] = ('date', 'location', 'new_cases', 'new_deaths', 'total_cases', 'total_deaths')
  # inFile[1] = [(date, location, new_cases, new_deaths, total_cases, total_deaths)]
  # rawData[country][date] = (newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases)
  rawData = {}
  with open(filepath) as inFile:
    for iRow, row in enumerate(csv.reader(inFile)):
      # Ignore first line in file
      if iRow == 0: continue
      dateString, country, newCases, newDeaths, totalCases, totalDeaths = row
      # Parse data
      newCases = 0 if newCases=='' else int(newCases)
      newDeaths = 0 if newDeaths=='' else int(newDeaths)
      totalCases = 0 if totalCases=='' else int(totalCases)
      totalDeaths = 0 if totalDeaths=='' else int(totalDeaths)
      # Append data
      if country not in rawData:
        rawData[country] = {}
      date= datetime.datetime.strptime(dateString,'%Y-%m-%d')
      rawData[country][date] = ([newCases, newDeaths, None, totalCases, totalDeaths, None, None])

  # Sort data
  # data[country][date] = (newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases)
  data = collections.OrderedDict()
  for country in sorted(rawData.keys()):
    for date in sorted(rawData[country].keys()):
      if country not in data:
        data[country] = collections.OrderedDict()
      data[country][date] = rawData[country][date]

  return data

def getDataFromJohnHopkins(dataFolder='./', tag=''):
  if not os.path.exists(dataFolder): os.makesdir(dataFolder)
  # Get time series data
  links = [
      "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv",
      "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv",
      "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv",
      ]
  # Download files
  files = []
  for url in links:
    filename = tag+os.path.basename(url)
    filepath = os.path.join(dataFolder,filename)
    files.append(filepath)
    # Gets data from url
    inFile = urllib2.urlopen(url)
    # Saves data
    tempData = inFile.read().decode('utf-8')
    print('Saving '+url+' to '+filepath)
    with open(filepath,'w') as outFile:
      outFile.write(tempData)

  # Collect rawData from files
  # rawData[country][date] = (newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases)
  rawData = {}
  for inFilePath in files:
    combineCountries = {
        'China': ['Mainland China'],
        'South Korea':['Korea, South', 'Republic of Korea'],
        'Taiwan':['Taiwan*'],
        }
    with open(inFilePath) as inFile:
      inFile = open(inFilePath)
      filename = os.path.basename(inFilePath)
      # inFile = [Province/State,Country/Region,Latitude,Longitude, CasesForDate...]
      for iRow, row in enumerate(csv.reader(inFile)):
        # Parse first line in csv
        if iRow == 0: 
          dates = row[4:]
          continue
        region = row[0]
        country = row[1]
        cases = row[4:]
        # Combine countries
        for combineCountry in combineCountries:
          if country in combineCountries[combineCountry]:
            country = combineCountry
        # Append data
        for iDate, date in enumerate(dates):
          date = datetime.datetime.strptime(date,'%m/%d/%y')
          case = 0 if cases[iDate]=="" else int(cases[iDate])
          if country not in rawData:
            rawData[country] = {}
          if date not in rawData[country]:
            rawData[country][date] = [0,0,0,0,0,0,0]
          # Collect region results to country
          if "time_series_19-covid-Confirmed" in filename:
            rawData[country][date][3] += case
          if "time_series_19-covid-Deaths" in filename:
            rawData[country][date][4] += case
          if "time_series_19-covid-Recovered" in filename:
            rawData[country][date][5] += case

  # Sort data
  # data[country][date] = (newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases)
  data = collections.OrderedDict()
  for country in sorted(rawData.keys()):
    for date in sorted(rawData[country].keys()):
      if country not in data:
        data[country] = collections.OrderedDict()
      data[country][date] = rawData[country][date]

  # Calculate new case and active cases
  for country in data:
    for iDate in range(len(data[country])):
      date = list(data[country].keys())[iDate]
      newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases = data[country][date]
      data[country][date] = [newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalCases - totalRecoveries]
      if iDate == 0: continue
      previousDate = list(data[country].keys())[iDate-1]
      previousNewCases, previousNewDeaths, previousNewRecoveries, previousTotalCases, previousTotalDeaths, previousTotalRecoveries, previousTotalActiveCases = data[country][previousDate]
      data[country][date] = [totalCases - previousTotalCases, totalDeaths - previousTotalDeaths, totalRecoveries - previousTotalRecoveries, totalCases, totalDeaths, totalRecoveries, totalCases - totalRecoveries]

  return data

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='Makes coronavirus graphs depending on countries. By default uses ourworldindata.')
  parser.add_argument('--jh', default=False, action='store_true', help='Use John Hopkins data')
  parser.add_argument('--wd', default=False, action='store_true', help='Use ourworldindata data')
  parser.add_argument('--outputFolder', default='./', help='Folder to store data and results')
  parser.add_argument('--png', default=False, action='store_true', help='Make plots with png')
  parser.add_argument('--dateTag', default=False, action='store_true', help='Add date tag to output files')
  args = parser.parse_args()

  # Handle arguments
  # Set dataType
  if args.wd: dataType = "WorldInData"
  elif args.jh: dataType = "JohnHopkins"
  else: dataType = "WorldInData"
  # Set plotExtension
  if args.png: plotExtension = 'png'
  else: plotExtension = 'pdf'
  # Set tag
  if args.dateTag: outputTag = datetime.datetime.now().strftime('%Y%m%d')+"_"
  else: outputTag = '' 

  # Gets data from source
  # data[country][date] = (newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases)
  if dataType == "WorldInData": 
    data = getDataFromWorldInData(dataFolder=args.outputFolder, tag=outputTag)
  if dataType == "JohnHopkins":
    data = getDataFromJohnHopkins(dataFolder=args.outputFolder, tag=outputTag)

  # Printing country names
  print('Countries: '+', '.join(data.keys()))

  # Plots countries that have a daily increase of above lowLimitCase
  #
  # Can set countries one is interested in. Below is an example.
  # interestedCountries = ["China", "Italy", "Iran", "South Korea", "Germany", "United States", "Switzerland"]
  #
  # data[country][date] = (0: newCases, 1: newDeaths, 2: newRecoveries, 3: totalCases, 4: totalDeaths, 5: totalRecoveries, 6: totalActiveCases)
  # interestedIndex: the index in data to use for plotting
  interestedCountries = []
  if dataType == "WorldInData":
    drawCases(data, interestedIndex=3, title="Total Cases", filename=os.path.join(args.outputFolder,outputTag+'TotalCasesWD.'+plotExtension), 
      lowLimitCase=150, interestedCountries=interestedCountries)
    drawCases(data, interestedIndex=4, title="Total Deaths", filename=os.path.join(args.outputFolder,outputTag+'TotalDeathsWD.'+plotExtension), 
      lowLimitCase=7, interestedCountries=interestedCountries)
  if dataType == "JohnHopkins":
    drawCases(data, interestedIndex=3, title="Total Cases", filename=os.path.join(args.outputFolder,outputTag+'TotalCasesJH.'+plotExtension), 
      lowLimitCase=150, interestedCountries=interestedCountries)
    drawCases(data, interestedIndex=4, title="Total Deaths", filename=os.path.join(args.outputFolder,outputTag+'TotalDeathsJH.'+plotExtension), 
      lowLimitCase=7, interestedCountries=interestedCountries)
    drawCases(data, interestedIndex=5, title="Total Recoveries", filename=os.path.join(args.outputFolder,outputTag+'TotalRecoveriesJH.'+plotExtension), 
      lowLimitCase=10, interestedCountries=interestedCountries)
    drawCases(data, interestedIndex=6, title="Total Active Cases", filename=os.path.join(args.outputFolder,outputTag+'TotalActiveCasesJH.'+plotExtension), 
      lowLimitCase=150, interestedCountries=interestedCountries)
