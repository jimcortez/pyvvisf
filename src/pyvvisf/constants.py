"""Constants and type definitions for pyvvisf."""

from . import vvisf_bindings as _vvisf

# ISF Value Type Constants
ISFValType_None = _vvisf.ISFValType_None
ISFValType_Event = _vvisf.ISFValType_Event
ISFValType_Bool = _vvisf.ISFValType_Bool
ISFValType_Long = _vvisf.ISFValType_Long
ISFValType_Float = _vvisf.ISFValType_Float
ISFValType_Point2D = _vvisf.ISFValType_Point2D
ISFValType_Color = _vvisf.ISFValType_Color
ISFValType_Cube = _vvisf.ISFValType_Cube
ISFValType_Image = _vvisf.ISFValType_Image
ISFValType_Audio = _vvisf.ISFValType_Audio
ISFValType_AudioFFT = _vvisf.ISFValType_AudioFFT

# ISF File Type Constants
ISFFileType_None = _vvisf.ISFFileType_None
ISFFileType_Source = _vvisf.ISFFileType_Source
ISFFileType_Filter = _vvisf.ISFFileType_Filter
ISFFileType_Transition = _vvisf.ISFFileType_Transition
ISFFileType_All = _vvisf.ISFFileType_All

# Utility functions
isf_val_type_to_string = _vvisf.isf_val_type_to_string
isf_file_type_to_string = _vvisf.isf_file_type_to_string 