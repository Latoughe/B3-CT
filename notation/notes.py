#!/usr/bin/python3
import sys
import re
import argparse

notes_file = './notes_file'
time_file = './groups_time'
groups = {}

criterias = ['pres_quality','problematique', 'challenge', 'answer_demo']
criterias_string = { 
        criterias[0]:'Qualité de la présentation',
        criterias[1]:'Choix et explication de la problématique',
        criterias[2]:'Challenge recherché',
        criterias[3]:'Réponse à la problématique et démo' }

class colors:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


def parse():
    notes = open(notes_file, "r")

    current_group_number = 0
    for lines in notes:
    
        if re.match('^G', lines):
            
            current_group_number = lines[1]
            groups[current_group_number] = {}
            groups[current_group_number]['marks'] = {}
            for criteria in criterias:
                groups[current_group_number]['marks'][criteria] = []
            
            current_group_members = []
            for member in lines.split(','):
                if re.match('^G[0-9]$', member):
                    continue
                else:
                    current_group_members.append(member.strip())
    
            groups[current_group_number]['members'] = current_group_members
    
    notes.close()
    notes = open(notes_file, "r")
    
    for lines in notes:
        if not re.match('^G', lines):
            
            rated_group = lines.split(':')[0]
    
            i=1
            for criteria in criterias:
                groups[rated_group]['marks'][criteria].append(lines.split(':')[i].strip())
                i=i+1
    
    notes.close()
    
    
    times = open(time_file, "r")
    for lines in times:
        current_group_number = lines.split(',')[0]
        current_group_time = lines.split(',')[1].strip()
    
        groups[current_group_number]['time'] = current_group_time
    
    times.close()
    
    
    for group in groups:
    
        groups[group]['averages'] = {}
    
        for criteria in criterias:
    
            average = 0
            mark_count = 0
    
            for mark in groups[group]['marks'][criteria]:
                average = average + float(mark)
                mark_count = mark_count + 1
    
            groups[group]['averages'][criteria] = (average / mark_count) * 4 # *4 to get a /20 mark (instead of /5)
    
        general = 0
        for criteria in criterias:
            general = general + groups[group]['averages'][criteria] 
    
        groups[group]['averages']['general'] = round(general / len(criterias), 2)

def print_group(group_number):
    print()
    print(colors.BOLD + "Group " + group_number + " : " + colors.END + ', '.join(groups[group_number]['members']))
    print("Time : " + groups[group_number]['time'] + " minutes")
    print("Notes :")
    
    for criteria in criterias:
        print("   - " + criterias_string[criteria] + " : " +
                ', '.join(groups[group_number]['marks'][criteria]) + 
                ' -> ' + str(groups[group_number]['averages'][criteria]))
    print('   - General : ' + str(groups[group_number]['averages']['general']))
    print()

def print_all():
    print()

    for group in groups:
        print("Group " + group + " : " + ', '.join(groups[group]['members']) +
                " : " + str(groups[group]['averages']['general']))

    print()


def stats():
    print()

    average_per_criteria = {}

    print("Quelques stats :")
    print()

    print(colors.BOLD + "  - Moyennes par critère :" + colors.END)
    for criteria in criterias:
        current_average = 0
        mark_count = 0
        for group in groups:
            current_average = current_average + groups[group]['averages'][criteria]
            mark_count = mark_count + 1

        average_per_criteria[criteria] = round(current_average / mark_count, 2)

        print("    > " + criterias_string[criteria] + 
            " : " + str(average_per_criteria[criteria]))

    
    print(colors.BOLD + "  - Time :" + colors.END)
    average_time = 0

    for group in groups:
        average_time = average_time + int(groups[group]['time'])
    average_time = average_time / len(groups)

    print("    > average : " + str(average_time) + " minutes")

    print()

###

parse()

parser = argparse.ArgumentParser()

parser.add_argument('-g', action='store', dest='group_number',
                    help='number of group you want to get the notes of')

parser.add_argument('-a', action='store_true', dest='all',
                    help='print all groups and general average')

parser.add_argument('-s', action='store_true', dest='stats',
                    help='print some stats')

args = parser.parse_args()

if args.all:
    print_all()
    sys.exit(0)

elif args.stats:
    stats()
    sys.exit(0)

elif args.group_number:
    print_group(args.group_number)
    sys.exit(0)

else:
    parser.print_help()
    sys.exit(0)


#print_group(arg)

