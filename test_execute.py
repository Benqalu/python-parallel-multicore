from parallel import Parallel

cmd_list=['python test_main.py' for i in range(0,10)]

pool=Parallel(p=4)
pool.add_cmd(cmd_list)
pool.run()
