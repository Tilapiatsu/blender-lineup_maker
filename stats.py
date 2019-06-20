import bpy

class Stats(object):
    def __init__(self, item):
        self.item = item
        self.data = self.item.data

    @property
    def triangle_count(self):
        triangle_count = 0

        for face in self.data.polygons:
            vertices = face.vertices
            triangles = len(vertices) - 2
            triangle_count += triangles

        return triangle_count

    @property
    def vertex_count(self):
        vertices = []
        for vertex in self.data.vertices:
            pos = [vertex.co[0], vertex.co[1], vertex.co[2]]
            vertices.append(pos)

        return len(vertices)
    
    @property
    def edge_count(self):
        edges = []
        for edge in self.data.edges:
            edges.append([edge.vertices[0], edge.vertices[1]])

        return len(edges)

    @property
    def has_uv2(self):
        has_uv = len(self.data.uv_layers)

        return has_uv > 1
