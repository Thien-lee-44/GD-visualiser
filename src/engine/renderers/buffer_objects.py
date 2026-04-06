"""
Wrapper for OpenGL Buffer Objects (VAO, VBO, EBO).
Handles the upload of geometric data to the GPU.
"""
import numpy as np
from OpenGL.GL import *
import ctypes 
from typing import List, Optional

class BufferObject:
    """Encapsulates OpenGL buffers for rendering vertices and indices."""
    
    def __init__(self, vertices: List[float], indices: Optional[List[int]] = None, vertex_size: int = 8) -> None:
        self.vertex_size = vertex_size 
        self.vertices = np.array(vertices, dtype=np.float32)
        self.has_vertex_color = (vertex_size >= 11)
        
        if indices is not None and len(indices) > 0:
            self.indices = np.array(indices, dtype=np.uint32)
        else:
            self.indices = None
            
        self.vao = int(np.array(glGenVertexArrays(1)).flatten()[0])
        glBindVertexArray(self.vao)
        
        self.vbo = int(np.array(glGenBuffers(1)).flatten()[0])
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        
        if self.indices is not None:
            self.ebo = int(np.array(glGenBuffers(1)).flatten()[0])
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        else:
            self.ebo = None
            
        stride = self.vertex_size * 4
        
        # Position attribute (X, Y, Z)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        
        # Normal attribute (Nx, Ny, Nz)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
        
        # Texture Coordinate attribute (U, V)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(6 * 4))
        
        # Vertex Color attribute (R, G, B)
        if self.has_vertex_color:
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8 * 4))
        else:
            glDisableVertexAttribArray(3)
            glVertexAttrib3f(3, -1.0, -1.0, -1.0) 
            
        glBindVertexArray(0)

    def draw(self) -> None:
        """Issues the GL draw call using the stored buffers."""
        glBindVertexArray(self.vao)
        if self.indices is not None:
            glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        else:
            glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // self.vertex_size)
        glBindVertexArray(0)
        
    def delete_buffers(self) -> None:
        """Frees GPU memory when the object is no longer needed."""
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(1, [self.vbo])
        if self.ebo is not None: 
            glDeleteBuffers(1, [self.ebo])