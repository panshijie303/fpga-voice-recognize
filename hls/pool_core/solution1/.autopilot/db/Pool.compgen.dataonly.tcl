# This script segment is generated automatically by AutoPilot

set axilite_register_dict [dict create]
set port_AXILiteS {
ap_start { }
ap_done { }
ap_ready { }
ap_idle { }
CHin_V { 
	dir I
	width 16
	depth 1
	mode ap_none
	offset 16
	offset_end 23
}
Hin_V { 
	dir I
	width 16
	depth 1
	mode ap_none
	offset 24
	offset_end 31
}
Win_V { 
	dir I
	width 16
	depth 1
	mode ap_none
	offset 32
	offset_end 39
}
Kx_V { 
	dir I
	width 8
	depth 1
	mode ap_none
	offset 40
	offset_end 47
}
Ky_V { 
	dir I
	width 8
	depth 1
	mode ap_none
	offset 48
	offset_end 55
}
mode_V { 
	dir I
	width 2
	depth 1
	mode ap_none
	offset 56
	offset_end 63
}
feature_in { 
	dir I
	width 32
	depth 1
	mode ap_none
	offset 64
	offset_end 71
}
feature_out { 
	dir I
	width 32
	depth 1
	mode ap_none
	offset 72
	offset_end 79
}
}
dict set axilite_register_dict AXILiteS $port_AXILiteS


