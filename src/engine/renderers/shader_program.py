"""
Wrapper for OpenGL Shader Program compilation and uniform management.
"""
import os
import glm
from OpenGL.GL import *
from typing import Any

class ShaderProgram:
    """Compiles GLSL shaders and provides methods to set uniform variables."""
    
    def __init__(self, vertex_path: str, fragment_path: str) -> None:
        v_src = self._read_file(vertex_path)
        f_src = self._read_file(fragment_path)
        self.program = self._compile_shaders(v_src, f_src)

    def _read_file(self, filepath: str) -> str:
        """Reads shader source code from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Shader file not found: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _compile_shaders(self, v_src: str, f_src: str) -> int:
        """Compiles and links the vertex and fragment shaders."""
        v_shader = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(v_shader, v_src)
        glCompileShader(v_shader)
        
        f_shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(f_shader, f_src)
        glCompileShader(f_shader)
        
        prog = glCreateProgram()
        glAttachShader(prog, v_shader)
        glAttachShader(prog, f_shader)
        glLinkProgram(prog)
        
        glDeleteShader(v_shader)
        glDeleteShader(f_shader)
        return prog

    def use(self) -> None:
        """Activates the shader program for subsequent rendering commands."""
        glUseProgram(self.program)

    def set_mat4(self, name: str, mat: glm.mat4) -> None:
        """Sends a 4x4 matrix uniform to the shader."""
        loc = glGetUniformLocation(self.program, name)
        glUniformMatrix4fv(loc, 1, GL_FALSE, glm.value_ptr(mat))

    def set_vec3(self, name: str, vec: Any) -> None:
        """Sends a 3D vector uniform to the shader."""
        loc = glGetUniformLocation(self.program, name)
        if hasattr(vec, 'x'): 
            glUniform3f(loc, vec.x, vec.y, vec.z)
        else: 
            glUniform3f(loc, float(vec[0]), float(vec[1]), float(vec[2]))

    def set_float(self, name: str, val: float) -> None:
        """Sends a float uniform to the shader."""
        loc = glGetUniformLocation(self.program, name)
        glUniform1f(loc, float(val))

    def set_int(self, name: str, val: int) -> None:
        """Sends an integer uniform to the shader."""
        loc = glGetUniformLocation(self.program, name)
        glUniform1i(loc, int(val))