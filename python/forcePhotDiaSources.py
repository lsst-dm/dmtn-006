
from __future__ import print_function, division

import lsst
import lsst.meas.base as measBase
import lsst.afw.table as afwTable
import lsst.pipe.base as pipeBase
import pdb

class TaskRunnerWithArgs(pipeBase.ButlerInitializedTaskRunner):
    @staticmethod
    def getTargetList(parsedCmd, **kwargs):
        return pipeBase.TaskRunner.getTargetList(parsedCmd,
                                                 templateExpRef=parsedCmd.templateExpID.refList,
                                                 **kwargs)

class ForcedPhotDiaSourcesConfig(lsst.pex.config.Config):
    """!Config class for forced measurement driver task."""

    measurement = lsst.pex.config.ConfigurableField(
        target=measBase.ForcedMeasurementTask,
        doc="subtask to do forced measurement"
        )
    def setDefaults(self):
        # TransformedCentroid takes the centroid from the reference catalog and uses it.
        self.measurement.plugins.names = ["base_TransformedCentroid", "base_PsfFlux"]
        self.measurement.slots.shape = None

class ForcedPhotDiaSourcesTask(pipeBase.CmdLineTask):

    ConfigClass = ForcedPhotDiaSourcesConfig
    RunnerClass = TaskRunnerWithArgs
    _DefaultName = "ForcedPhotDiaSourcesTask"

    def __init__(self, butler=None, **kwargs):
        super(lsst.pipe.base.CmdLineTask, self).__init__(**kwargs)

        # We need an example output table from diffim measurement to load.
        visits = butler.queryMetadata("deepDiff_diaSrc", "visit")
        ccds = butler.queryMetadata("deepDiff_diaSrc", "ccdnum", visit=visits[0])
        example_table = butler.get("deepDiff_diaSrc", visit=visits[0], ccdnum=ccds[0])

        self.refSchema = example_table.getSchema()
        self.makeSubtask("measurement", refSchema=self.refSchema)
        self.dataPrefix = ""


    def run(self, diaSourceRef, templateExpRef=None):
        """ Perform forced photometry on the science and template exposures that went into a DiaSrc.
        """

        butler = diaSourceRef.getButler()
        exposure = butler.get("calexp", dataId=diaSourceRef.dataId)
        refWcs = exposure.getWcs()

        refCat =  diaSourceRef.get() #self.fetchReferences(exposure)
        measCat = self.measurement.generateMeasCat(exposure, refCat, refWcs)

        #self.log.info("Performing forced measurement on science image %s" % scienceExpRef.dataId)

        self.measurement.attachTransformedFootprints(measCat, refCat, exposure, refWcs)
        self.measurement.run(measCat, exposure, refCat, refWcs)

        #
        # Now we rerun measurement on the template exposure.
        #
        templateId = diaSourceRef.dataId.copy()
        #pdb.set_trace()
        templateId['visit'] = templateExpRef[0].dataId['visit']
        template_exposure = butler.get("calexp", dataId=templateId)

        #self.log.info("Performing forced measurement on science image %s" % scienceExpRef.dataId)
        template_measCat = self.measurement.generateMeasCat(template_exposure,
                                                            refCat, refWcs)
        self.measurement.attachTransformedFootprints(template_measCat, refCat,
                                                     template_exposure, refWcs)
        self.measurement.run(template_measCat, template_exposure, refCat, refWcs)


        #
        # Measure the diffim
        #
        diffim_exposure = butler.get("deepDiff_differenceExp", dataId=diaSourceRef.dataId)

        diffim_measCat = self.measurement.generateMeasCat(diffim_exposure,
                                                            refCat, refWcs)
        self.measurement.attachTransformedFootprints(diffim_measCat, refCat,
                                                     diffim_exposure, refWcs)
        self.measurement.run(diffim_measCat, diffim_exposure, refCat, refWcs)

        #
        # Set up a table mapper so we can add the (upcoming) template measurement
        # results to a new output table
        #
        mapper = afwTable.SchemaMapper(measCat.schema)
        mapper.addMinimalSchema(measCat.schema, True)
        mapper.editOutputSchema().addField("classification_dipole", type=int)
        mapper.editOutputSchema().addField("template_base_PsfFlux_flux", type=float)
        mapper.editOutputSchema().addField("template_base_PsfFlux_fluxSigma", type=float)
        mapper.editOutputSchema().addField("diffim_base_PsfFlux_flux", type=float)
        mapper.editOutputSchema().addField("diffim_base_PsfFlux_fluxSigma", type=float)


        newMeasCat = afwTable.SourceCatalog(mapper.getOutputSchema())
        newMeasCat.extend(measCat, mapper=mapper)

        newMeasCat['template_base_PsfFlux_flux'][:] = template_measCat['base_PsfFlux_flux']
        newMeasCat['template_base_PsfFlux_fluxSigma'][:] = template_measCat['base_PsfFlux_fluxSigma']

        newMeasCat['diffim_base_PsfFlux_flux'][:] = diffim_measCat['base_PsfFlux_flux']
        newMeasCat['diffim_base_PsfFlux_fluxSigma'][:] = diffim_measCat['base_PsfFlux_fluxSigma']

        newMeasCat['classification_dipole'][:] = refCat['classification_dipole']

        self.writeOutput(diaSourceRef, newMeasCat)

    def writeOutput(self, dataRef, sources):
        """!Write forced source table
        @param dataRef  Data reference from butler; the forced_src dataset (with self.dataPrefix included)
                        is all that will be modified.
        @param sources  SourceCatalog to save
        """
        dataRef.put(sources, self.dataPrefix + "forced_src")

    @classmethod
    def _makeArgumentParser(cls):
        parser = lsst.pipe.base.ArgumentParser(name=cls._DefaultName)

        # Can I make an argument which is a dataset type?
        parser.add_id_argument("--id", "deepDiff_diaSrc", help="data ID of the Dia source catalog")
        parser.add_id_argument("--templateExpID", "calexp",
                               help="template visit ID, e.g. --templateExpID visit=6789")
        return parser

    # Overriding these two functions prevent the task from attempting to save the config.
    def _getConfigName(self):
        return None
    def _getMetadataName(self):
        return None


if __name__ == "__main__":

    ForcedPhotDiaSourcesTask.parseAndRun()

