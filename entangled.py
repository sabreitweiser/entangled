'''
Entangled: The world's first Quantum dating algorithm!
By Alex Breitweiser for PennApps XVI, Fall 2017
'''



###IBM QX Imports###

# Checking the version of PYTHON; we only support 3 at the moment
import sys
if sys.version_info < (3,0):
    raise Exception('Please use Python version 3 or greater.')
    
# useful additional packages 
import matplotlib.pyplot as plt
#%matplotlib inline
import numpy as np


import sys
sys.path.append('/Users/sabreitweiser/qiskit-sdk-py/') #Change to point to your qiskit root

# importing the QISKit
from qiskit import QuantumCircuit, QuantumProgram
import Qconfig

# import basic plot tools
from qiskit.tools.visualization import plot_histogram


###Tinder API imports###
sys.path.append('/Users/sabreitweiser/Tinder/') #Change to point to your Tinder api root
from features import get_match_info, pause
from tinder_api import authverif, like, dislike, get_recommendations, get_person

###My imports###
from queue import Queue
from pprint import pprint
from urllib.request import urlopen
from PIL import Image
from time import sleep
from datetime import date
from random import random

###Helper code###
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

###Setting up Tinder###
authverif()

###Setting up IBMQX###
device = 'ibmqx2' # the device to run on
device = 'local_qasm_simulator' # uncomment to run on the simulator
batch_size = 50 # Number of decisions in one request

QPS_SPECS = {
    "name": "decision",
    "circuits": [{
        "name": "decision_circuit",
        "quantum_registers": [{
            "name":"q",
            "size":1
        }],
        "classical_registers": [{
            "name":"c",
            "size":1
        }]}]
}

Q_program = QuantumProgram(specs=QPS_SPECS)
Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])

# Quantum circuits to generate decisions
circuits = ["decision"+str(i) for i in range(batch_size)]
# NB: Can't have more than one measurement per circuit
for circuit in circuits:
    q = Q_program.get_quantum_register("q")
    c = Q_program.get_classical_register('c')
    decision_circuit = Q_program.create_circuit(circuit, [q], [c])
    decision_circuit.h(q[0]) #Turn the qubit into |0> + |1>
    decision_circuit.measure(q[0], c[0])
_ = Q_program.get_qasms(circuits) # Suppress the output

###Main Loop###
recommendations = Queue() #Queue to hold tinder recommendations
decisions = Queue() #Queue to hold QX decisions

while True:
	#Replenish the queues
	if recommendations.empty():
		results = get_recommendations()
		results = results['results']
		for key in results:
			recommendations.put(key['_id'])

	if decisions.empty():
		results = Q_program.execute(circuits, device, shots=1,
						max_credits=5, wait=10,
						timeout=240)
		for ciruit in circuits:
			for key in results.get_counts(ciruit):
				decisions.put(int(key))


	#Match a decision to a recommendation
	rec = recommendations.get()
	dec = decisions.get()
	
	print('ID: ' + rec)
	person = get_person(rec)
	person = person['results']
	print('NAME: ' + person['name'])
	if person.get('jobs'):
		for job in person['jobs']:
			if job.get('company'):
				print('COMPANY: ' + job['company']['name'])
			if job.get('title'):
				print('TITLE: ' + job['title']['name'])

	if person.get('schools'):
		for school in person['schools']:
			print('SCHOOL: ' + school['name'])

	if person.get('bio'):
		print('BIO: ' + person['bio'])

	if person.get('distance_mi'):
		print('DISTANCE: ' + str(person['distance_mi']) + ' miles')

	for photo in person['photos']:
		URL = photo['url']
		with urlopen(URL) as url:
			with open('temp.jpg', 'wb') as f:
				f.write(url.read())

		img = Image.open('temp.jpg')
		img.show()
	
	if dec:
		like(rec)
		print(bcolors.OKGREEN + 'LIKED' + bcolors.ENDC)
	else:
		dislike(rec)
		print(bcolors.FAIL + 'DISLIKED' + bcolors.ENDC)

	for _ in range(5):
		sleep(4*random())
		print('...')
