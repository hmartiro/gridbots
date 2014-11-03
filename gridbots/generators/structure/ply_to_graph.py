"""

"""

import sys


def ply_to_graph(ply_file):

    #print('Parsing structure from ply file: {}'.format(ply_file))

    # Read the file into a list of lines
    with open(ply_file) as file:
        ply_data = file.read().splitlines()

    # Get the number of vertex/normal pairs and faces
    num_vertex_normals = -1
    num_faces = -1
    for line in ply_data:
        if line.startswith('element vertex'):
            num_vertex_normals = int(line.split(' ')[2])
        elif line.startswith('element face'):
            num_faces = int(line.split(' ')[2])
    #print('Number of vertex/normal elements: {}'.format(num_vertex_normals))

    # Get the start point of the vertex list
    start_inx = ply_data.index('end_header') + 1

    # Parse unique vertices
    vertices = []
    for i in range(start_inx, start_inx + num_vertex_normals):
        vertex = [float(p) for p in ply_data[i].split(' ')[:3]]
        #d = [float(p) for p in ply_data[i].split(' ')[:3]]
        #print(i)
        if vertex not in vertices:
            vertices.append(vertex)

    num_vertices = len(vertices)
    print('Number of unique vertices: {}'.format(num_vertices))

    # Create a dictionary of vertices by giving IDs
    vertex_dict = {i: v for i, v in enumerate(vertices)}

    print('Number of faces: {}'.format(num_faces))

    # Parse edges from faces
    edges = []
    i0 = start_inx + num_vertex_normals
    for i in range(i0, i0 + num_faces):

        face_v_n_ids = [int(v) for v in ply_data[i].split(' ')[1:]]

        face_v_ids = []
        for vertex_normal_id in face_v_n_ids:
            vertex = [float(p) for p in ply_data[start_inx + vertex_normal_id].split(' ')[:3]]
            face_v_ids.append(vertices.index(vertex))

        for j in range(len(face_v_ids)):
            v0 = face_v_ids[j]
            v1 = face_v_ids[(j+1) % len(face_v_ids)]
            if [v0, v1] not in edges and [v1, v0] not in edges:
                edges.append([v0, v1])

    # Return vertices and edges
    return vertex_dict, edges


if __name__ == '__main__':

    f = sys.argv[1]
    vertices, edges = ply_to_graph(f)

    output = {'vertices': vertices, 'edges': edges}

    import yaml
    print(yaml.dump(output))
