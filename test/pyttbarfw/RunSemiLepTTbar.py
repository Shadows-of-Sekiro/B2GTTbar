#! /usr/bin/env python


## _________                _____.__                            __  .__               
## \_   ___ \  ____   _____/ ____\__| ____  __ ______________ _/  |_|__| ____   ____  
## /    \  \/ /  _ \ /    \   __\|  |/ ___\|  |  \_  __ \__  \\   __\  |/  _ \ /    \ 
## \     \___(  <_> )   |  \  |  |  / /_/  >  |  /|  | \// __ \|  | |  (  <_> )   |  \
##  \______  /\____/|___|  /__|  |__\___  /|____/ |__|  (____  /__| |__|\____/|___|  /
##         \/            \/        /_____/                   \/                    \/ 
import sys
import math
import array as array
from optparse import OptionParser

from B2GTTreeSemiLep import B2GTTreeSemiLep
import B2GSelectSemiLepTTbar_Type2, B2GSelectSemiLepTTbar_IsoStd


import ROOT


class RunSemiLepTTbar() :
    '''
    Driver class for Semileptonic TTbar analyses.
    This will use "Selection" classes (the first below is B2GSelectSemiLepTTbar)
    that return a bitset of cuts at different phases. This class can then
    make plots at those stages of selection.

    The factorization allows different drivers to use the same selection classes
    with the same bitsets, or to use different selections to use the same histogramming
    functionality.


    '''
    

    def __init__(self, argv ) : 

        ###
        ### Get the command line options
        ###
        parser = OptionParser()

        parser.add_option('--infile', type='string', action='store',
                          dest='infile',
                          default = '',
                          help='Input file string')


        parser.add_option('--outfile', type='string', action='store',
                          dest='outfile',
                          default = '',
                          help='Output file string')

        parser.add_option('--tau21Cut', type='float', action='store',
                          dest='tau21Cut',
                          default = 0.7,
                          help='Tau 21 cut')

        parser.add_option('--tau32Cut', type='float', action='store',
                          dest='tau32Cut',
                          default = 0.7,
                          help='Tau 32 cut')
        
        parser.add_option('--bdiscmin', type='float', action='store',
                          dest='bdiscmin',
                          default = 0.7,
                          help='B discriminator cut')

        parser.add_option('--maxevents', type='int', action='store',
                          dest='maxevents',
                          default = None,
                          help='Maximum number of events')
        
        parser.add_option('--ignoreTrig', action='store_true',
                          dest='ignoreTrig',
                          default = False,
                          help='Ignore the trigger?')
        

        (options, args) = parser.parse_args(argv)
        argv = []



        self.outfile = ROOT.TFile(options.outfile, "RECREATE")

        ### Create the tree class. This will make simple class members for each
        ### of the branches that we want to read from the Tree to save time.
        ### Also saved are some nontrivial variables that involve combinations
        ### of things from the tree
        self.treeobj = B2GTTreeSemiLep( options )


        print 'Getting entries'
        entries = self.treeobj.tree.GetEntries()
        if options.maxevents == None or options.maxevents < 0 : 
            self.eventsToRun = entries
        else : 
            self.eventsToRun = min( options.maxevents, entries )

        ### Here is the semileptonic ttbar selection for W jets
        self.lepSelection = B2GSelectSemiLepTTbar_IsoStd.B2GSelectSemiLepTTbar_IsoStd( options, self.treeobj )
        self.hadSelection = B2GSelectSemiLepTTbar_Type2.B2GSelectSemiLepTTbar_Type2( options, self.treeobj, self.lepSelection )

        self.nstages = self.lepSelection.nstages + self.hadSelection.nstages
        self.nlep = 2 # Electrons and muons

        ### Book histograms
        self.book()

    '''
    Coarse flow control. Loops over events, reads, and fills histograms. 
    Try not to modify anything here if you add something.
    Add whatever you can in "book" and "fill". If you need to add something
    complicated, cache it as a member variable in the Selector class you're interested
    in, and just make simple plots here. 
    '''
    def run(self):
        
        print 'processing ', self.eventsToRun, ' events'

        for jentry in xrange( self.eventsToRun ):
            if jentry % 10000 == 0 :
                print 'processing ' + str(jentry)
            # get the next tree in the chain and verify            
            ientry = self.treeobj.tree.GetEntry( jentry )        
            # Select events, get the bitset corresponding to the cut flow
            passbitsLep = self.lepSelection.select()
            passbitsHad = self.hadSelection.select()
            passbits = passbitsLep + passbitsHad
            # For each stage in the cut flow, make plots
            for ipassbit in xrange( len(passbits) ) :
                if passbits[ipassbit] :
                    self.fill( ipassbit )

        # Wrap it up. 
        print 'Finished looping'
        self.close()
        print 'Closed'



        
    def book( self ) :
        '''
        Book histograms, one for each stage of the selection. 
        '''
        self.outfile.cd()

        self.LeptonPtHist = []
        self.LeptonEtaHist = []
        self.METPtHist = []
        self.HTLepHist = []
        self.Iso2DHist = []
        
        self.AK8PtHist = []
        self.AK8EtaHist = []
        self.AK8MHist = []
        self.AK8MSDHist = []
        self.AK8MSDSJ0Hist = []
        self.lepNames = ['Electron', 'Muon' ]

        self.hists = []
        for ilep in xrange(self.nlep) :
            self.AK8PtHist.append([])
            self.AK8EtaHist.append([])
            self.AK8MHist.append([])
            self.AK8MSDHist.append([])
            self.AK8MSDSJ0Hist.append([])

            self.LeptonPtHist.append([])
            self.LeptonEtaHist.append([])

            self.METPtHist.append([])
            self.HTLepHist.append([])
            self.Iso2DHist.append([])

                
            for ival in xrange(self.nstages):
                self.AK8PtHist[ilep].append( ROOT.TH1F("AK8PtHist" + self.lepNames[ilep] + str(ival), "Jet p_{T}, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, 0, 1000) )
                self.AK8EtaHist[ilep].append( ROOT.TH1F("AK8EtaHist" + self.lepNames[ilep] + str(ival), "Jet #eta, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, -2.5, 2.5) )
                self.AK8MHist[ilep].append( ROOT.TH1F("AK8MHist" + self.lepNames[ilep] + str(ival), "Jet Mass, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, 0, 500) )
                self.AK8MSDHist[ilep].append( ROOT.TH1F("AK8MSDHist" + self.lepNames[ilep] + str(ival), "Jet Soft Dropped Mass, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, 0, 500) )
                self.AK8MSDSJ0Hist[ilep].append( ROOT.TH1F("AK8MSDSJ0Hist" + self.lepNames[ilep] + str(ival), "Leading Subjet Soft Dropped Mass, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, 0, 500) )

                self.LeptonPtHist[ilep].append( ROOT.TH1F("LeptonPtHist" + self.lepNames[ilep] + str(ival), "Lepton p_{T}, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, 0, 1000) )
                self.LeptonEtaHist[ilep].append( ROOT.TH1F("LeptonEtaHist" + self.lepNames[ilep] + str(ival), "Lepton #eta, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, -2.5, 2.5) )

                self.METPtHist[ilep].append( ROOT.TH1F("METPtHist" + self.lepNames[ilep] + str(ival), "Missing p_{T}, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, 0, 1000) )
                self.HTLepHist[ilep].append( ROOT.TH1F("HTLepHist" + self.lepNames[ilep] + str(ival), "Lepton p_{T} + Missing p_{T}, " + self.lepNames[ilep] + ", Stage " + str(ival), 1000, 0, 1000) )
                self.Iso2DHist[ilep].append ( ROOT.TH2F("Iso2DHist" + self.lepNames[ilep] + str(ival), "Lepton 2D isolation (#Delta R vs p_{T}^{REL} ), " + self.lepNames[ilep] + ", Stage " + str(ival), 25, 0, 500, 25, 0, 1) )

            

    def fill( self, index ) :
        '''
        Fill the histograms we're interested in. If you're doing something complicated, make a
        member variable in the Selector class to cache the variable and just fill here. 
        '''
        a = self.lepSelection
        b = self.hadSelection
        ilep = a.tree.LeptonIsMu[0]
        print 'ilep = ', ilep
        if b.ak8Jet != None :
            self.AK8PtHist[ilep][index].Fill( b.ak8Jet.Perp() )
            self.AK8EtaHist[ilep][index].Fill( b.ak8Jet.Eta() )
            self.AK8MHist[ilep][index].Fill( b.ak8Jet.M() )
            self.AK8MSDHist[ilep][index].Fill( b.ak8SDJet.M() )
            self.AK8MSDSJ0Hist[ilep][index].Fill( b.ak8SDJet_Subjet0.M() )

        if a.leptonP4 != None : 
            self.LeptonPtHist[ilep][index].Fill( a.leptonP4.Perp() )
            self.LeptonEtaHist[ilep][index].Fill( a.leptonP4.Eta() )
            self.METPtHist[ilep][index].Fill( a.nuP4.Perp() )
            self.HTLepHist[ilep][index].Fill( a.leptonP4.Perp() + a.nuP4.Perp() )
            if a.ak4Jet != None : 
                self.Iso2DHist[ilep][index].Fill( a.leptonP4.Perp( a.ak4Jet.Vect() ), a.leptonP4.DeltaR( a.ak4Jet ) )
            


    def close( self ) :
        '''
        Wrap it up. 
        '''
        self.outfile.cd() 
        self.outfile.Write()
        self.outfile.Close()


'''
        Executable
'''
if __name__ == "__main__" :
    r = RunSemiLepTTbar(sys.argv)
    r.run()
