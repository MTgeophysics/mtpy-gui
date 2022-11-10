# mtpy-gui
GUI Interface to work with MTpy for visualizing and manipulating data and models

## Functionality (TODO)

- Have a main dashboard with access to all GUI's
- Runs MTpy v2 behind the scenes which uses `MTH5` and `mt_metadata`
- Visualize a data set by station
  - Apparent resistivity, phase, tipper
  - Phase tensor representation
- Visualize a data set in map view
  - Apparent resitivity and phase maps per period
  - Phase tensor ellipses with induction vectors per period
    - Would be nice to scale these by penetration depth
  - Depth of penetration
- Create model data and mesh files from transfer function files and MTH5's
  - ModEM
  - SimPEG
  - Mare2DEM
  - Occam?
  - Others
- Visualize model results: Data
  - Per station apparent resistivity, phase, tipper
  - Phase tensor maps + residual
  - Misfits 
    - Statistics (histograms)
      - Per period
      - Per station
      - Per component
    - Map view per period per component
 - Visualize model results: Model
   - Profiles
   - Depth slices
   - 3D views
     - Cut profiles
     - Isosurfaces
     - Cropping
     
  
