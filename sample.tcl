
    proc DisplayErrorAndCloseConnection {socketID code APIName} {
    global tcl_argv
    if {$code == -2} {
        set error_message "$APIName ERROR => -2 : TCP timeout"
    } elseif {$code == -108} {
        set error_message "$APIName ERROR => -108 : The TCP/IP connection was closed by an administrator"
    } else {
        set code2 [catch {ErrorStringGet $socketID $code strError}]
        if {$code2 != 0} {
            set error_message "$APIName ERROR => $code - ErrorStringGet ERROR => $code2"
        } else {
            set error_message "$APIName $strError"
        }
    }
    puts stdout $error_message
    set tcl_argv(0) $error_message
    catch {TCP_CloseSocket $socketID}
    return
}

####################
set TimeOut 40
set code 0

OpenConnection $TimeOut socketID
if {$socketID == -1} {
    puts stdout "OpenConnection failed => -1"
    return
}   
        set code [GroupMoveAbsolute $socketID "Group3" 0 0 ]
        
        after 100
        
        set code [catch "MultipleAxesPVTVerification  $socketID Group3 sample.pvt"]
        if {$code != 0} {
            DisplayErrorAndCloseConnection $socketID $code "MultipleAxesPVTVerification"
            return
        }
        
        set code [catch "MultipleAxesPVTExecution $socketID Group3 sample.pvt 1"]
        if {$code != 0} {
            DisplayErrorAndCloseConnection $socketID $code "MultipleAxesPVTExecution"
            return
        }
        