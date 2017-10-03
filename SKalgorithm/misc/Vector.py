import math

def add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]

def sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def cross(a, b):
    return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]

def mult(a, x):
    return [a*x[0], a*x[1], a*x[2]]

def normalize(x):
    return mult(1/math.sqrt(dot(x, x)), x)

def norm(a):
    return math.sqrt(dot(a, a))

def project(x, y):
    unit = normalize(y)
    return mult(dot(x, unit), unit)
