#!/usr/bin/env python
import ROOT
import urllib2
import csv
import array
import collections
import re
import os
import glob
import datetime
import argparse

# Plots countries that have a daily increase of above lowLimitCase
# dayLimit sets the number of days to plot
# maxCase sets the maximum number of cases to plot
def drawCases(data, interestedIndex=4, title="Total Cases", filename='totalCases.pdf', dayLimit=-1, lowLimitCase=200, maxCase = -1, interestedCountries=[], ignoreCountries=['Worldwide', 'International conveyance (Diamond Princess)', 'International', 'Others', 'World', 'Cruise Ship'], maxExcludeCountry = ['China']):
  # Collect interested data depending on rowIndex. Sort country by number of cases
  # data[country][date] = (newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases)
  # interestData[country][date] = case
  interestData = collections.OrderedDict()
  for country in sorted(data, key=lambda c: max(data[c].values()[-1]), reverse=True):
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

  # Convert to rootDataFormat
  # interestDataRoot[country] = ([iDay],[case])
  interestDataRoot = collections.OrderedDict()
  for country in interestData:
    for iDate, date in enumerate(interestData[country]):
      if country not in interestDataRoot: interestDataRoot[country] = [array.array('d'), array.array('d')]
      interestDataRoot[country][0].append(iDate)
      interestDataRoot[country][1].append(interestData[country][date])

  # Draw settings
  canvas = ROOT.TCanvas("c"+title,"c"+title,500,500)
  markers = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34]
  colors = [1, 2, 3, 4, 6, 7, 8, 9]

  # Make TGraphs
  graphs = collections.OrderedDict()
  for iCountry, country in enumerate(interestDataRoot):
    entries = len(interestDataRoot[country][0])
    days = interestDataRoot[country][0]
    cases = interestDataRoot[country][1]
    graph = ROOT.TGraph(entries, days, cases)
    graph.SetTitle(country)
    graph.SetName(country)
    graphs[country] = graph

  # Make TSpline from TGraphs to process graphs more dynamically
  sgraphs = collections.OrderedDict()
  maxEntry = 0
  minEntry = 0
  maxDays = 0
  legend = ROOT.TLegend(0.15, 0.4, 0.35, 0.9)
  for iGraph, (country, graph) in enumerate(graphs.items()):
    xArray = array.array('d')
    yArray = array.array('d')
    spline = ROOT.TSpline5("s"+country, graph)
    nPoints = graph.GetN()
    passIncreasePoint = lowLimitCase
    hasPassed = False
    countPoints = 0
    offset = 0
    # Make data from TSpline
    # Append days only after passing increase threshold
    for iPoint in xrange(nPoints):
      if iPoint != nPoints-1 : 
        increase = spline.Eval(iPoint+1)-spline.Eval(iPoint)
        if increase > passIncreasePoint:
          hasPassed = True
      # Has passed increase threshold
      if hasPassed:
        # Append data
        xArray.append(countPoints)
        yArray.append(spline.Eval(iPoint))
        # Find y max and x max
        if country not in maxExcludeCountry:
          # Limit number of days
          if dayLimit == -1 or countPoints < dayLimit:
            minEntry = min([minEntry, min(yArray)])
            maxEntry = max([maxEntry, max(yArray)])
            maxDays = max([maxDays, max(xArray)])
        countPoints += 1
    # If there is data passing increase threshold make TGraph
    if countPoints!= 0:
      sgraph = ROOT.TGraph(countPoints, xArray, yArray)
      sgraph.SetTitle(graph.GetTitle())
      sgraph.SetMarkerStyle(markers[iGraph%len(markers)])
      sgraph.SetMarkerColor(colors[iGraph%len(colors)])
      sgraph.SetLineColor(colors[iGraph%len(colors)])
      legend.AddEntry(sgraph,sgraph.GetTitle(),"lp")
      if len(sgraphs) == 0: 
        sgraph.Draw("APL")
      else: sgraph.Draw("PL")
      sgraphs[country] = sgraph

  # Graph settings
  sgraph = list(sgraphs.values())[0]
  if maxCase == -1 or maxEntry*1.2 < maxCase:
    sgraph.SetMaximum(maxEntry*1.2)
  else:
    sgraph.SetMaximum(maxCase)
  sgraph.SetMinimum(minEntry)
  sgraph.GetXaxis().SetLimits(0,maxDays+1)
  sgraph.GetXaxis().SetTitle("days")
  sgraph.GetYaxis().SetTitle("cases")
  sgraph.GetYaxis().SetTitleOffset(2)
  sgraph.SetTitle(title)
  canvas.SetLeftMargin(0.15)
  legend.Draw()

  canvas.SaveAs(filename)

def getDataFromWorldInData(dataFolder='./'):
  if not os.path.exists(dataFolder): os.makesdir(dataFolder)
  confirmedUrl = 'http://cowid.netlify.com/data/full_data.csv'
  filepath = os.path.join(dataFolder, os.path.basename(confirmedUrl))

  # Gets data from url
  inFile = urllib2.urlopen(confirmedUrl)
  # Saves data
  tempData = inFile.read()
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

def getDataFromJohnHopkins(dataFolder='./'):
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
    filename = os.path.basename(url)
    filepath = os.path.join(dataFolder,filename)
    files.append(filepath)
    # Gets data from url
    inFile = urllib2.urlopen(url)
    # Saves data
    tempData = inFile.read()
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
          case = int(cases[iDate])
          if country not in rawData:
            rawData[country] = {}
          if date not in rawData[country]:
            rawData[country][date] = [0,0,0,0,0,0,0]
          # Collect region results to country
          if filename == "time_series_19-covid-Confirmed.csv":
            rawData[country][date][3] += case
          if filename == "time_series_19-covid-Deaths.csv":
            rawData[country][date][4] += case
          if filename == "time_series_19-covid-Recovered.csv":
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
    for iDate in xrange(len(data[country])):
      date = data[country].keys()[iDate]
      newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases = data[country][date]
      data[country][date] = [newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalCases - totalRecoveries]
      if iDate == 0: continue
      previousDate = data[country].keys()[iDate-1]
      previousNewCases, previousNewDeaths, previousNewRecoveries, previousTotalCases, previousTotalDeaths, previousTotalRecoveries, previousTotalActiveCases = data[country][previousDate]
      data[country][date] = [totalCases - previousTotalCases, totalDeaths - previousTotalDeaths, totalRecoveries - previousTotalRecoveries, totalCases, totalDeaths, totalRecoveries, totalCases - totalRecoveries]

  return data

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description='Makes coronavirus graphs depending on countries. By default uses ourworldindata.')
  parser.add_argument('--jh', default=False, action='store_true', help='Use John Hopkins data')
  parser.add_argument('--wd', default=False, action='store_true', help='Use ourworldindata data')
  parser.add_argument('--outputFolder', default='./', help='Folder to store data and results')
  args = parser.parse_args()

  if args.wd: dataType = "WorldInData"
  elif args.jh: dataType = "JohnHopkins"
  else: dataType = "WorldInData"

  # Gets data from source
  # data[country][date] = (newCases, newDeaths, newRecoveries, totalCases, totalDeaths, totalRecoveries, totalActiveCases)
  if dataType == "WorldInData": 
    data = getDataFromWorldInData(dataFolder=args.outputFolder)
  if dataType == "JohnHopkins":
    data = getDataFromJohnHopkins(dataFolder=args.outputFolder)

  print('Countries: '+', '.join(data.keys()))

  # Plots countries that have a daily increase of above lowLimitCase
  # Can set countries one is interested in. Below is an example.
  #interestedCountries = ["China", "Italy", "Iran", "South Korea", "Germany", "United States", "Switzerland"]
  interestedCountries = []
  if dataType == "WorldInData":
    drawCases(data, interestedIndex=3, title="Total Cases", filename=os.path.join(args.outputFolder,'TotalCasesWD.pdf'), 
      lowLimitCase=150, interestedCountries=interestedCountries)
    drawCases(data, interestedIndex=4, title="Total Deaths", filename=os.path.join(args.outputFolder,'TotalDeathsWD.pdf'), 
      lowLimitCase=7, interestedCountries=interestedCountries)
  if dataType == "JohnHopkins":
    drawCases(data, interestedIndex=3, title="Total Cases", filename=os.path.join(args.outputFolder,'TotalCasesJH.pdf'), 
      lowLimitCase=150, interestedCountries=interestedCountries)
    drawCases(data, interestedIndex=4, title="Total Deaths", filename=os.path.join(args.outputFolder,'TotalDeathsJH.pdf'), 
      lowLimitCase=7, interestedCountries=interestedCountries)
    drawCases(data, interestedIndex=5, title="Total Recoveries", filename=os.path.join(args.outputFolder,'TotalRecoveriesJH.pdf'), 
      lowLimitCase=10, interestedCountries=interestedCountries)
    drawCases(data, interestedIndex=6, title="Total Active Cases", filename=os.path.join(args.outputFolder,'TotalActiveCasesJH.pdf'), 
      lowLimitCase=150, interestedCountries=interestedCountries)
