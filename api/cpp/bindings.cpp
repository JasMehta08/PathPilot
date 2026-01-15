#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "pathfinder.cpp" // Direct include for simplicity in single-file build

namespace py = pybind11;

PYBIND11_MODULE(cpp_pathfinder, m) {
    m.doc() = "Fast C++ Pathfinding Extension using A*";

    m.def("astar", &astar_cpp, "Run A* algorithm",
          py::arg("num_nodes"),
          py::arg("row_ptr"),
          py::arg("cols"),
          py::arg("weights"),
          py::arg("x_coords"),
          py::arg("y_coords"),
          py::arg("start_node"),
          py::arg("goal_node"));
}
