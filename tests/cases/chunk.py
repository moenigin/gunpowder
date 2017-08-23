from .provider_test import ProviderTest
from gunpowder import *
import numpy as np

class ChunkTestSource(BatchProvider):

    def get_spec(self):
        spec = ProviderSpec()
        spec.volumes[VolumeTypes.RAW] = Roi((20000,2000,2000), (2000,200,200))
        spec.volumes[VolumeTypes.GT_LABELS] = Roi((20100,2010,2010), (1800,180,180))
        return spec

    def provide(self, request):

        # print("ChunkTestSource: Got request " + str(request))

        batch = Batch()

        # have the pixels encode their position
        for (volume_type, roi) in request.volumes.items():

            roi_voxel = roi // volume_type.voxel_size
            # print("ChunkTestSource: Adding " + str(volume_type))

            # the z,y,x coordinates of the ROI
            meshgrids = np.meshgrid(
                    range(roi_voxel.get_begin()[0], roi_voxel.get_end()[0]),
                    range(roi_voxel.get_begin()[1], roi_voxel.get_end()[1]),
                    range(roi_voxel.get_begin()[2], roi_voxel.get_end()[2]), indexing='ij')
            data = meshgrids[0] + meshgrids[1] + meshgrids[2]

            # print("Roi is: " + str(roi))

            batch.volumes[volume_type] = Volume(
                    data,
                    roi)
        return batch

class TestChunk(ProviderTest):

    def test_output(self):

        voxel_size = (20, 2, 2)
        register_volume_type(VolumeType('RAW', interpolate=True, voxel_size=voxel_size))
        register_volume_type(VolumeType('GT_LABELS', interpolate=False, voxel_size=voxel_size))

        source = ChunkTestSource()

        raw_roi    = source.get_spec().volumes[VolumeTypes.RAW]
        labels_roi = source.get_spec().volumes[VolumeTypes.GT_LABELS]

        chunk_request = BatchRequest()
        chunk_request.add_volume_request(VolumeTypes.RAW, (400,30,34))
        chunk_request.add_volume_request(VolumeTypes.GT_LABELS, (200,10,14))

        full_request = BatchRequest({
                VolumeTypes.RAW: raw_roi,
                VolumeTypes.GT_LABELS: labels_roi
            }
        )

        pipeline = ChunkTestSource() + Chunk(chunk_request)

        with build(pipeline):
            batch = pipeline.request_batch(full_request)

        # assert that pixels encode their position
        for (volume_type, volume) in batch.volumes.items():

            vx_size = volume_type.voxel_size
            # the z,y,x coordinates of the ROI
            meshgrids = np.meshgrid(
                    range(volume.roi.get_begin()[0]//vx_size[0], volume.roi.get_end()[0]//vx_size[0]),
                    range(volume.roi.get_begin()[1]//vx_size[1], volume.roi.get_end()[1]//vx_size[1]),
                    range(volume.roi.get_begin()[2]//vx_size[2], volume.roi.get_end()[2]//vx_size[2]), indexing='ij')
            data = meshgrids[0] + meshgrids[1] + meshgrids[2]

            self.assertTrue((volume.data == data).all())

        assert(batch.volumes[VolumeTypes.RAW].roi.get_offset() == (20000, 2000, 2000))

        # restore default volume types
        voxel_size = (1,1,1)
        register_volume_type(VolumeType('RAW', interpolate=True, voxel_size=voxel_size))
        register_volume_type(VolumeType('GT_LABELS', interpolate=False, voxel_size=voxel_size))

