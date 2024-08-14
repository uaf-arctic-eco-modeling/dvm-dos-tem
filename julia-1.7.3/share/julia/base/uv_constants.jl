const uv_handle_types = [:UV_ASYNC, :UV_CHECK, :UV_FS_EVENT, :UV_FS_POLL, :UV_HANDLE, :UV_IDLE, :UV_NAMED_PIPE, :UV_POLL, :UV_PREPARE, :UV_PROCESS, :UV_STREAM, :UV_TCP, :UV_TIMER, :UV_TTY, :UV_UDP, :UV_SIGNAL, :UV_FILE]
const uv_req_types = [:UV_REQ, :UV_CONNECT, :UV_WRITE, :UV_SHUTDOWN, :UV_UDP_SEND, :UV_FS, :UV_WORK, :UV_GETADDRINFO, :UV_GETNAMEINFO, :UV_RANDOM,]
const uv_err_vals = [(:UV_E2BIG,(-(7))), (:UV_EACCES,(-(13))), (:UV_EADDRINUSE,(-(98))), (:UV_EADDRNOTAVAIL,(-(99))), (:UV_EAFNOSUPPORT,(-(97))), (:UV_EAGAIN,(-(11))), (:UV_EAI_ADDRFAMILY,(-3000)), (:UV_EAI_AGAIN,(-3001)), (:UV_EAI_BADFLAGS,(-3002)), (:UV_EAI_BADHINTS,(-3013)), (:UV_EAI_CANCELED,(-3003)), (:UV_EAI_FAIL,(-3004)), (:UV_EAI_FAMILY,(-3005)), (:UV_EAI_MEMORY,(-3006)), (:UV_EAI_NODATA,(-3007)), (:UV_EAI_NONAME,(-3008)), (:UV_EAI_OVERFLOW,(-3009)), (:UV_EAI_PROTOCOL,(-3014)), (:UV_EAI_SERVICE,(-3010)), (:UV_EAI_SOCKTYPE,(-3011)), (:UV_EALREADY,(-(114))), (:UV_EBADF,(-(9))), (:UV_EBUSY,(-(16))), (:UV_ECANCELED,(-(125))), (:UV_ECHARSET,(-4080)), (:UV_ECONNABORTED,(-(103))), (:UV_ECONNREFUSED,(-(111))), (:UV_ECONNRESET,(-(104))), (:UV_EDESTADDRREQ,(-(89))), (:UV_EEXIST,(-(17))), (:UV_EFAULT,(-(14))), (:UV_EFBIG,(-(27))), (:UV_EHOSTUNREACH,(-(113))), (:UV_EINTR,(-(4))), (:UV_EINVAL,(-(22))), (:UV_EIO,(-(5))), (:UV_EISCONN,(-(106))), (:UV_EISDIR,(-(21))), (:UV_ELOOP,(-(40))), (:UV_EMFILE,(-(24))), (:UV_EMSGSIZE,(-(90))), (:UV_ENAMETOOLONG,(-(36))), (:UV_ENETDOWN,(-(100))), (:UV_ENETUNREACH,(-(101))), (:UV_ENFILE,(-(23))), (:UV_ENOBUFS,(-(105))), (:UV_ENODEV,(-(19))), (:UV_ENOENT,(-(2))), (:UV_ENOMEM,(-(12))), (:UV_ENONET,(-(64))), (:UV_ENOPROTOOPT,(-(92))), (:UV_ENOSPC,(-(28))), (:UV_ENOSYS,(-(38))), (:UV_ENOTCONN,(-(107))), (:UV_ENOTDIR,(-(20))), (:UV_ENOTEMPTY,(-(39))), (:UV_ENOTSOCK,(-(88))), (:UV_ENOTSUP,(-(95))), (:UV_EOVERFLOW,(-(75))), (:UV_EPERM,(-(1))), (:UV_EPIPE,(-(32))), (:UV_EPROTO,(-(71))), (:UV_EPROTONOSUPPORT,(-(93))), (:UV_EPROTOTYPE,(-(91))), (:UV_ERANGE,(-(34))), (:UV_EROFS,(-(30))), (:UV_ESHUTDOWN,(-(108))), (:UV_ESPIPE,(-(29))), (:UV_ESRCH,(-(3))), (:UV_ETIMEDOUT,(-(110))), (:UV_ETXTBSY,(-(26))), (:UV_EXDEV,(-(18))), (:UV_UNKNOWN,(-4094)), (:UV_EOF,(-4095)), (:UV_ENXIO,(-(6))), (:UV_EMLINK,(-(31))), (:UV_EHOSTDOWN,(-(112))), (:UV_EREMOTEIO,(-(121))), (:UV_ENOTTY,(-(25))), (:UV_EFTYPE,(-4028)), (:UV_EILSEQ,(-(84))), (:UV_ESOCKTNOSUPPORT,(-(94))),]
let
    handles = [:UV_UNKNOWN_HANDLE, uv_handle_types..., :UV_HANDLE_TYPE_MAX]
    reqs = [:UV_UNKNOWN_REQ, uv_req_types..., :UV_REQ_TYPE_PRIVATE, :UV_REQ_TYPE_MAX]
    for i in 1:length(handles)
        @eval const $(handles[i]) = $(i - 1)
    end
    for i in 1:length(reqs)
        @eval const $(reqs[i]) = $(i - 1)
    end
    for (v, val) in uv_err_vals
        @eval const $v = $val
    end
end
