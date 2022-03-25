"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""
        
__author__ = "Sam Wolk"
__version__ = "2022.03.23"

ghenv.Component.Name = "Kangaroo2LiveSolver"
ghenv.Component.NickName ="K2LS"
        
import rhinoscriptsyntax as rs
import Grasshopper as gh
import json
import random
import time

def updateComponent():
    """ Updates this component, similar to using a grasshopper timer """
    
    # Define callback action
    def callBack(e):
        ghenv.Component.ExpireSolution(False)
        
        
    # Get grasshopper document
    ghDoc = ghenv.Component.OnPingDocument()
    
    # Schedule this component to expire
    ghDoc.ScheduleSolution(2000,gh.Kernel.GH_Document.GH_ScheduleDelegate(callBack))

def computeSim(geometry,parameters):
    print("start sim")
    cluster = gh.Kernel.Special.GH_Cluster()
    cluster.CreateFromFilePath("C:\Users\Sam Wolk\Dropbox\mit\design-optimization\EUI_Computer_Cluster.ghcluster")
    for i in range(len(geometry)):
        cluster.Params.Input[0].AddVolatileData(gh.Kernel.Data.GH_Path(0), i,geometry[i])
    cluster.Params.Input[1].AddVolatileData(gh.Kernel.Data.GH_Path(0), 0, parameters)
    doc = gh.Kernel.GH_Document()
    print("quarter sim")
    doc.Enabled = True
    print("split")
    doc.AddObject(cluster, True, 0)
    print("three eighths sim")
    structure = cluster.Params.Output[0].VolatileData
    tree = gh.DataTree[object]()
    print("mid sim")
    tree.MergeStructure(structure, gh.Kernel.Parameters.Hints.GH_NullHint())
    cost = tree.Branch(0)[0].Value
    structure = cluster.Params.Output[2].VolatileData
    tree = gh.DataTree[object]()
    tree.MergeStructure(structure, gh.Kernel.Parameters.Hints.GH_NullHint())
    eui = tree.Branch(0)[0].Value
    doc.Enabled = False
    doc.RemoveObject(cluster, False)
    doc.Dispose()
    doc = None
    print("end sim")
    return eui,cost


parameterMetadata = {
    'envelope' : {
        'roofs' : {'min':0,'max':2,'steps':3},
        'floors' : {'min':0,'max':1,'steps':2},
        'tightness':{'min':0,'max':1,'steps':2},
        'walls':{'min':0,'max':3,'steps':4}
    },
    'hvac':{
        'source':{'min':0,'max':2,'steps':3},
        'hrv':{'min':0,'max':1,'steps':2},
        'fans':{'min':0,'max':1,'steps':2}
    },
    'lighting':{
        'dimming':{'min':0,'max':1,'steps':2},
        'type':{'min':0,'max':1,'steps':2}
    },
    'wwr':{
    's':{'min':0,'max':1,'steps':20},
        'e':{'min':0,'max':1,'steps':20},
        'w':{'min':0,'max':1,'steps':20},
        'n':{'min':0,'max':1,'steps':20}
    },
}

if 'baseline' not in globals() and run:
    start = time.time()
    eui,cost = computeSim(geometry, buildingParameters)
    duration = time.time() - start
    baseline = {'eui':eui, 'cost':cost, 'duration':duration}
    baselineResults = json.dumps(baseline)
    
if 'results' not in globals():
    results = []
    
if 'firstOrderComplete' not in globals(): 
    firstOrderComplete = False

if 'fixedParameters' not in globals():
    fixedParameters = []
    
if 'firstOrderParametersToTest' not in globals():
    firstOrderParametersToTest = []
    for (category,parameters) in parameterMetadata.items():
        for (parameter,data) in parameters.items():
            value = data['max']
            parameterToTest = {'category':category,'parameter':parameter,'value':value}
            firstOrderParametersToTest.append(parameterToTest)
    random.shuffle(firstOrderParametersToTest)

testParameters = json.loads(buildingParameters)

if len(firstOrderParametersToTest) > 0 and run:
    parameterToTest = firstOrderParametersToTest.pop(0)
    category = parameterToTest['category']
    param = parameterToTest['parameter']
    testParameters[category][param] = parameterToTest['value']
    start = time.time()
    eui,cost = computeSim(geometry,json.dumps(testParameters))
    duration = time.time() - start
    result = {}
    result['category'] = parameterToTest['category']
    result['parameter'] = parameterToTest['parameter']
    result['value'] = parameterToTest['value']
    result['eui'] = eui
    result['cost'] = cost
    result['duration'] = duration
    result['euiDelta'] = eui-baseline['eui']
    result['costDelta'] = cost-baseline['cost']
    result['durationDelta'] = duration - baseline['duration']
    result['efficacy'] = result['euiDelta'] / (result['costDelta'] if result['costDelta'] != 0 else 1)
    results.append(result)

out = json.dumps(results)
results.sort(key = lambda res : res['efficacy'])

if len(firstOrderParametersToTest) == 0 and len(results)>0 and not firstOrderComplete:
    firstOrderComplete = True

if firstOrderComplete and len(fixedParameters) < 1:
    pass

    
efficacies = [result['efficacy'] for result in results]
labels = [result['parameter'] for result in results]
euis = [result['eui'] for result in results]
costs = [result['cost'] for result in results]

if run:
    updateComponent()


