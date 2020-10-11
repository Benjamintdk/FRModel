from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from xml.etree import ElementTree

import gdal
import numpy as np
import pandas as pd
from laspy.file import File


@dataclass
class Cloud3D:

    f: File
    lat: float
    long: float
    origin_x: float
    origin_y: float
    origin_z: float

    @staticmethod
    def from_las_xml(las_path:str, xml_path:str) -> Cloud3D:
        f = File(las_path, mode='r')

        lat, long, origin_x, origin_y, origin_z = Cloud3D._read_xml(xml_path)
        return Cloud3D(f, lat, long, origin_x, origin_y, origin_z)

    def data(self, sample_size=None, transformed=True):
        data = np.random.choice(self.f.points, sample_size, False) if sample_size else self.f.points
        data2 = pd.DataFrame(data['point'][['X', 'Y', 'Z', 'red', 'green', 'blue']]).to_numpy()
        if transformed: data2 = Cloud3D._transform_data(data2, self.header)
        return deepcopy(data2)

    @property
    def header(self):
        return self.f.header

    def close(self):
        self.f.close()

    @staticmethod
    def get_geo_info(geotiff_path: str):
        ds = gdal.Open(geotiff_path)
        xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()

        return dict(xoffset=xoffset, px_w=px_w, rot1=rot1,
                    yoffset=yoffset, px_h=px_h, rot2=rot2)

    def write_las(self, file_name: str, alt_header:File = None):
        """ Writes the current points in a las format

        Header used will be the same as the one provided during loading otherwise given.
        """

        f = File(file_name, mode='w', header=alt_header if alt_header else self.header)
        data = self.data(transformed=False)

        f.X = data[:, 0]
        f.Y = data[:, 1]
        f.Z = data[:, 2]

        f.Red   = data[:, 3]
        f.Green = data[:, 4]
        f.Blue  = data[:, 5]

        f.close()
        
    @staticmethod
    def _transform_data(data, header: File):
        """ Transforms data suitable for usage, from LAS format """
        return np.hstack([Cloud3D._transform_xyz(data[:, :3], header),
                          Cloud3D._transform_rgb(data[:, 3:])])

    @staticmethod
    def _inv_transform_data(data, header: File):
        """ Transforms data suitable for writing """
        return np.hstack([Cloud3D._inv_transform_xyz(data[:, :3], header),
                          Cloud3D._inv_transform_rgb(data[:, 3:])])

    @staticmethod
    def _transform_xyz(xyz, header: File):
        """ Transforms XYZ according to the header information

        This transforms XYZ into a workable, intended format for usage.
        """
        # noinspection PyUnresolvedReferences
        return xyz + [o / s for o, s in zip(header.offset, header.scale)]

    @staticmethod
    def _transform_rgb(rgb):
        """ Transforms RGB according to the header information

        This transforms RGB into 0 - 255
        """
        return rgb // (2 ** 8)

    @staticmethod
    def _inv_transform_xyz(xyz, header: File):
        """ Inverse Transforms XYZ according to the header information

        This inverse transforms XYZ according to header, intended for writing
        """
        # noinspection PyUnresolvedReferences
        return xyz - [o / s for o, s in zip(header.offset, header.scale)]

    @staticmethod
    def _inv_transform_rgb(rgb):
        """ Inverse Transforms RGB according to the header information

        This transforms RGB into 0 - 65535, intended for writing
        """
        return rgb * (2 ** 8)

    @staticmethod
    def _read_xml(xml_path):
        """ Reads XML and returns

        :param xml_path: Path to XML metadata
        :returns: Latitude, Longitude, Origin X, Y, Z respectively
        """
        root = ElementTree.parse(xml_path).getroot()
        return [float(i) for i in root[0].text[4:].split(",")] + [float(i) for i in root[1].text.split(",")]

#
#
# #
# las_A = File(f'../rsc/las/cloud_A.las', mode='r')
# las_A_samp = File(f'../rsc/las/cloud_A_samp.las', mode='w', header=las_A.header)
# las_A_samp.points = np.random.choice(las_A.points,PTS,False)
#
# las_X = File(f'../rsc/las/cloud_X.las', mode='r')
# las_X_samp = File(f'../rsc/las/cloud_X_samp.las', mode='w', header=las_X.header)
# las_X_samp.points = np.random.choice(las_X.points,PTS,False)
#
# las = File(f'../rsc/las/cloud_samp.las', mode='w', header=las_A.header)
#
# las_A_samp.X = las_A_samp.X + las_A.header.offset[0] / las_A.header.scale[0]
# las_A_samp.Y = las_A_samp.Y + las_A.header.offset[1] / las_A.header.scale[1]
# las_A_samp.Z = las_A_samp.Z + las_A.header.offset[2] / las_A.header.scale[2]
#
# las_X_samp.X = las_X_samp.X + las_X.header.offset[0] / las_A.header.scale[0]
# las_X_samp.Y = las_X_samp.Y + las_X.header.offset[1] / las_A.header.scale[1]
# las_X_samp.Z = las_X_samp.Z + las_X.header.offset[2] / las_A.header.scale[2]
#
# las_A.close()
# las_X.close()
#
# las.points = np.append(las_A_samp.points, las_X_samp.points)
#
# ar = np.vstack([las.X, las.Y, las.Z, las.Red, las.Green, las.Blue]).transpose()
# ar[:,3:] = ar[:,3:] * 255 / (2**16)
#
# df = pd.DataFrame(ar, columns=['X','Y','Z','R','G','B'])
#
# trace= go.Scatter3d(x=df.X,
#                     y=df.Y,
#                     z=df.Z,
#                     mode='markers',
#                     marker=dict(size=1.25,
#                                 color=['rgb({},{},{})'.format(r, g, b) for r, g, b in
#                                        zip(df.R.values, df.G.values, df.B.values)],
#                                 opacity=0.9))
#
# data = [trace]
#
# layout = go.Layout(margin=dict(l=0,
#                                r=0,
#                                b=0,
#                                t=0))
#
# fig = go.Figure(data=data, layout=layout)
# fig.update_layout(scene_aspectmode='data')
# fig.show()
# # # lasX = File('rsc/las/cloud_X.las', mode='r')
# # # [('point',
# # # [('X', '<i4'),
# # # ('Y', '<i4'),
# # # ('Z', '<i4'),
# # # ('intensity', '<u2'),
# # # ('flag_byte', 'u1'),
# # # ('raw_classification', 'u1'),
# # # ('scan_angle_rank', 'i1'),
# # # ('user_data', 'u1'),
# # # ('pt_src_id', '<u2'),
# # # ('red', '<u2'),
# # # ('green', '<u2'),
# # # ('blue', '<u2')])]
# # lasA
# #
# # CLUSTERS = 4
#
#
# # f = Frame2D.from_image("rsc/imgs/sample.jpg")
#
# # X Y H S V MEXG
# #
# # sns.set_palette(sns.color_palette("Blues"))
# # frame_xy = f.get_chns(xy=True, glcm=True,glcm_radius=10,glcm_verbose=True)
# # frame_xy.kmeans(clusters=4,
# #                 fit_indexes=[2,3,4,5,6,7,8,9,10],  # Means to grab H S V VEG
# #                 plot_figure=True,
# #                 #sample_weight=np.sum(frame_xy.data_flatten()[:,[0,1]], axis=1),
# #                 xy_indexes=(0,1),
# #                 scatter_size=0.4,
# #                 scaler=minmax_scale)
# #
# # plt.gca().set_aspect('equal')
# # plt.gca().invert_yaxis()
# # plt.gcf().set_size_inches(f.width()/96*2,f.height()/96*2)
# # plt.gcf().savefig('clusterma.jpg', dpi=96)
#
#
# # R     G     B     H     S     V     EX_G  MEX_G  EX_GR  NDI   VEG    X     Y    ConR  ConG  ConB  CorrR CorrG CorrB EntR  EntG  EntB
# # R        G        B        H        S        V        EX_G     MEX_G     EX_GR     NDI      VEG      EX_GR    X        Y        ConR     ConG     ConB     CorrR    CorrG    CorrB    EntR     EntG     EntB
#
# # np.savetxt('out3.csv', z.data.reshape([-1, z.data.shape[-1]]), fmt="%.3f", delimiter=',')
# # np.savetxt('out6.csv', z.data.reshape([-1, z.data.shape[-1]]), fmt="%.6f", delimiter=',')
#
