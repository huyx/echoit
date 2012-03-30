原来的 README 参见 README.orig.txt

这个在原来的基础上增加了两个参数的定制：

    echo 模块
        setup(write, method)

使用例子(使用在 Twisted 中)：

    from twisted.python import log
	import echo
	
	echo.setup(log.msg, '')
