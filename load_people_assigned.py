""" Main program that loads related people from a file

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-21
:Copyright: 2018, Arthur Goldberg
:License: MIT
Hannah Poisner Version
"""
import argparse
import logging
import os
import sys
import related_person
from related_person import Gender, RelatedPerson, RelatedPersonError

class LogFilter(logging.Filter):
    """code from https://stackoverflow.com/questions/1383254/logging-streamhandler-and-standard-streams
    """
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level

class Logger(object):
    """Creates the log instance to the program for the program
        and determines what type of logs are used
    """

    def __init__(self, error_handler):
        ## Creating std.out handler for verified people
        stdout_handler = logging.StreamHandler(sys.stdout)
        std_outfilter = LogFilter(logging.WARNING)
        stdout_handler.addFilter(std_outfilter)
        stdout_handler.setLevel(logging.DEBUG)
        ## creating the logger
        self.logger = logging.getLogger('People_Logger')
        ## setting the level for the logger
        self.logger.setLevel(logging.DEBUG)
        ## creating the handler
        self.error_handler = error_handler
        ## creating the formatter
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        self.error_handler.setFormatter(formatter)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)
        self.logger.addHandler(self.error_handler)

    @staticmethod
    def set_error_method(logfile):
        #Tests if logfile is none
        if logfile != None:
            ## If not none creates a logfile and adds to logger instance
            logfile_handler = logging.FileHandler(logfile)
            logfile_handler.setLevel(logging.ERROR)
            log = Logger(logfile_handler)
            return log
        elif logfile == None:
            ## If non creates a std_err logger and adds to logger instance
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.ERROR)
            log = Logger(stderr_handler)
            return log



class RawPersonRecord(object):
    FIELDS = 5
    def __init__(self, id, name, father_id, mother_id, gender, row):
        self.id = id
        self.name = name
        self.father_id = father_id
        self.mother_id = mother_id
        self.gender = gender
        self.row = row

    @staticmethod
    def make_from_line(line, row):
        l = line.strip().split('\t')
        if len(l) != RawPersonRecord.FIELDS:
            raise ValueError("row {}: has {} fields, not {}".format(row, len(l), RawPersonRecord.FIELDS))
        t = tuple(l+[row])
        return RawPersonRecord(*t)

class LoadPeople(object):
    NULL_ID = '0'

    def __init__(self):
        self.buffer = []
        self.people_index = {}

    @staticmethod
    def all_people(people_index):
        for id in sorted(people_index.keys()):
            print(str(people_index[id]))

    # todo: write phase1
    @staticmethod
    def phase1():
        # Phase 1
        """ Phase 1 creates a command-line interface that reads people from a file
        or standard input (stdin) (ask what he means)
        Obtains:
            An input file
            Optionally a file to which error messages should be written
        """
        parser = argparse.ArgumentParser(description="Files required for program")
        ## add something about fialed to open
        parser.add_argument('-f', '--filename', required=True, type=argparse.FileType('r'), help="Please provide a tab delimited file with related people.")
        parser.add_argument('-lf', '--logfile', required=False, type=str, help="Please provide a log file.")
        args = parser.parse_args()
        return args


    def phase2(self, filename, logfile, log):
        ## Phase 2 testing
        row = 0
        errors = []
        bad_ids = set()
        f = filename
        for line in f:
            row += 1
            try:
                self.buffer.append(RawPersonRecord.make_from_line(line, row))
            except ValueError as e:
                errors.append(str(e))
        ## he wrote this
        for raw_person in self.buffer:
            try:
                if raw_person.id in self.people_index:
                     bad_ids.add(raw_person.id)
                     del self.people_index[raw_person.id]
                if raw_person.id in bad_ids:
                    raise RelatedPersonError("duplicate ID: {}".format(raw_person.id))
                ## i wrote this
                raw_person_gender = raw_person.gender
                correct_constant = Gender.get_gender(raw_person_gender)
                gender = correct_constant
                related_person = RelatedPerson(raw_person.id, raw_person.name, raw_person.gender)
                self.people_index[raw_person.id] = related_person
            except RelatedPersonError as e:
                errors.append("row {}: {}".format(raw_person.row, str(e)))
        if errors:
            if logfile != None:
                for rpe in errors:
                    log.logger.error(rpe)
            elif logfile == None:
                log.logger.error('- individual errors -')
                log.logger.error('\n'.join(errors))


    def check_parent(self, raw_person, parent):
        if parent == 'mother':
            if raw_person.mother_id != LoadPeople.NULL_ID:
                if raw_person.mother_id not in self.people_index:
                    raise RelatedPersonError("{} missing mother {}".format(raw_person.id, raw_person.mother_id))
        elif parent == 'father':
            if raw_person.father_id != LoadPeople.NULL_ID:
                if raw_person.father_id not in self.people_index:
                    raise RelatedPersonError("{} missing father {}".format(raw_person.id, raw_person.father_id))

    def set_parent(self, raw_person, parent):
        related_person = self.people_index[raw_person.id]
        if parent == 'mother':
            if raw_person.mother_id != LoadPeople.NULL_ID:
                try:
                    mother = self.people_index[raw_person.mother_id]
                    related_person.set_mother(mother)
                except KeyError as RelatedPersonError:
                    return RelatedPersonError
        elif parent == 'father':
            if raw_person.father_id != LoadPeople.NULL_ID:
                try:
                    father = self.people_index[raw_person.father_id]
                    related_person.set_father(father)
                except KeyError as RelatedPersonError:
                    return RelatedPersonError

    def phase3(self, logfile, log):
        # Phase 3:
        errors = []
        bad_ids = set()

        for raw_person in self.buffer:
            if raw_person.id in self.people_index:
                # todo: check that the parents of raw_person exist; use check_parent() to help
                try:
                    self.check_parent(raw_person, "mother")
                except RelatedPersonError as e:
                    errors.append("row {}: {}".format(raw_person.row, str(e)))
                    bad_ids.add(raw_person.mother_id)
                try:
                    self.check_parent(raw_person,  "father")
                except RelatedPersonError as e:
                    errors.append("row {}: {}".format(raw_person.row, str(e)))
                    bad_ids.add(raw_person.father_id)
                #set parents, which checks their gender
                if raw_person.id not in bad_ids:
                    for parent in ['mother', 'father']:
                        try:
                            self.set_parent(raw_person, parent)
                        except RelatedPersonError as e: ## change error raised to RPE
                            errors.append("row {}: for {} {}".format(raw_person.row, raw_person.id, str(e)))
                            bad_ids.add(raw_person.id)
        # # delete all the RelatedPerson entries for the bad people
        for bad_id in bad_ids:
            del self.people_index[bad_id]

        # todo: write to output determined by command line input
        if errors:
            if logfile != None:
                for rpe in errors:
                    log.logger.error(rpe)
            elif logfile == None:
                log.logger.error('- relatedness errors -')
                log.logger.error('\n'.join(errors))

        # todo: create a log entry for each RelatedPerson that is verified
        log.logger.info('These are the verified people')
        for key, value in self.people_index.items():
            log.logger.info("{}: {}".format(key, value))




    def main(self, args, log):
        filename = args.filename
        logfile = args.logfile
        self.phase2(filename, logfile, log)
        self.phase3(logfile, log)
        return self.people_index

args = LoadPeople.phase1()
log = Logger.set_error_method(args.logfile)
LoadPeople().main(args, log)
