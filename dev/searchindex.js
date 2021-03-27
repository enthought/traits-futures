Search.setIndex({docnames:["api/traits_futures","api/traits_futures.api","api/traits_futures.background_call","api/traits_futures.background_iteration","api/traits_futures.background_progress","api/traits_futures.base_future","api/traits_futures.exception_handling","api/traits_futures.future_states","api/traits_futures.i_future","api/traits_futures.i_message_router","api/traits_futures.i_parallel_context","api/traits_futures.i_task_specification","api/traits_futures.multiprocessing_context","api/traits_futures.multiprocessing_router","api/traits_futures.multithreading_context","api/traits_futures.multithreading_router","api/traits_futures.null","api/traits_futures.null.gui_test_assistant","api/traits_futures.null.init","api/traits_futures.null.pinger","api/traits_futures.qt","api/traits_futures.qt.gui_test_assistant","api/traits_futures.qt.init","api/traits_futures.qt.pinger","api/traits_futures.toolkit_support","api/traits_futures.traits_executor","api/traits_futures.version","api/traits_futures.wrappers","api/traits_futures.wx","api/traits_futures.wx.gui_test_assistant","api/traits_futures.wx.init","api/traits_futures.wx.pinger","guide/advanced","guide/cancel","guide/intro","guide/testing","index"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":3,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":2,"sphinx.domains.rst":2,"sphinx.domains.std":2,"sphinx.ext.intersphinx":1,"sphinx.ext.viewcode":1,sphinx:56},filenames:["api/traits_futures.rst","api/traits_futures.api.rst","api/traits_futures.background_call.rst","api/traits_futures.background_iteration.rst","api/traits_futures.background_progress.rst","api/traits_futures.base_future.rst","api/traits_futures.exception_handling.rst","api/traits_futures.future_states.rst","api/traits_futures.i_future.rst","api/traits_futures.i_message_router.rst","api/traits_futures.i_parallel_context.rst","api/traits_futures.i_task_specification.rst","api/traits_futures.multiprocessing_context.rst","api/traits_futures.multiprocessing_router.rst","api/traits_futures.multithreading_context.rst","api/traits_futures.multithreading_router.rst","api/traits_futures.null.rst","api/traits_futures.null.gui_test_assistant.rst","api/traits_futures.null.init.rst","api/traits_futures.null.pinger.rst","api/traits_futures.qt.rst","api/traits_futures.qt.gui_test_assistant.rst","api/traits_futures.qt.init.rst","api/traits_futures.qt.pinger.rst","api/traits_futures.toolkit_support.rst","api/traits_futures.traits_executor.rst","api/traits_futures.version.rst","api/traits_futures.wrappers.rst","api/traits_futures.wx.rst","api/traits_futures.wx.gui_test_assistant.rst","api/traits_futures.wx.init.rst","api/traits_futures.wx.pinger.rst","guide/advanced.rst","guide/cancel.rst","guide/intro.rst","guide/testing.rst","index.rst"],objects:{"":{traits_futures:[0,0,0,"-"]},"traits_futures.background_call":{BackgroundCall:[2,1,1,""],CallBackgroundTask:[2,1,1,""],CallFuture:[2,1,1,""],submit_call:[2,4,1,""]},"traits_futures.background_call.BackgroundCall":{args:[2,2,1,""],background_task:[2,3,1,""],callable:[2,2,1,""],future:[2,3,1,""],kwargs:[2,2,1,""]},"traits_futures.background_iteration":{BackgroundIteration:[3,1,1,""],GENERATED:[3,5,1,""],IterationBackgroundTask:[3,1,1,""],IterationFuture:[3,1,1,""],submit_iteration:[3,4,1,""]},"traits_futures.background_iteration.BackgroundIteration":{args:[3,2,1,""],background_task:[3,3,1,""],callable:[3,2,1,""],future:[3,3,1,""],kwargs:[3,2,1,""]},"traits_futures.background_iteration.IterationFuture":{result_event:[3,2,1,""]},"traits_futures.background_progress":{BackgroundProgress:[4,1,1,""],PROGRESS:[4,5,1,""],ProgressBackgroundTask:[4,1,1,""],ProgressFuture:[4,1,1,""],ProgressReporter:[4,1,1,""],submit_progress:[4,4,1,""]},"traits_futures.background_progress.BackgroundProgress":{args:[4,2,1,""],background_task:[4,3,1,""],callable:[4,2,1,""],future:[4,3,1,""],kwargs:[4,2,1,""]},"traits_futures.background_progress.ProgressFuture":{progress:[4,2,1,""]},"traits_futures.background_progress.ProgressReporter":{report:[4,3,1,""]},"traits_futures.base_future":{BaseFuture:[5,1,1,""]},"traits_futures.base_future.BaseFuture":{cancel:[5,3,1,""],cancellable:[5,2,1,""],done:[5,2,1,""],exception:[5,3,1,""],result:[5,3,1,""],state:[5,2,1,""]},"traits_futures.exception_handling":{marshal_exception:[6,4,1,""]},"traits_futures.future_states":{CANCELLABLE_STATES:[7,5,1,""],CANCELLED:[7,5,1,""],CANCELLING:[7,5,1,""],COMPLETED:[7,5,1,""],DONE_STATES:[7,5,1,""],EXECUTING:[7,5,1,""],FAILED:[7,5,1,""],FutureState:[7,2,1,""],WAITING:[7,5,1,""]},"traits_futures.i_future":{IFuture:[8,1,1,""]},"traits_futures.i_future.IFuture":{cancel:[8,3,1,""],cancellable:[8,2,1,""],done:[8,2,1,""],exception:[8,3,1,""],message:[8,2,1,""],result:[8,3,1,""],state:[8,2,1,""]},"traits_futures.i_message_router":{IMessageReceiver:[9,1,1,""],IMessageRouter:[9,1,1,""],IMessageSender:[9,1,1,""]},"traits_futures.i_message_router.IMessageReceiver":{message:[9,2,1,""]},"traits_futures.i_message_router.IMessageRouter":{close_pipe:[9,3,1,""],pipe:[9,3,1,""],start:[9,3,1,""],stop:[9,3,1,""]},"traits_futures.i_message_router.IMessageSender":{send:[9,3,1,""],start:[9,3,1,""],stop:[9,3,1,""]},"traits_futures.i_parallel_context":{IParallelContext:[10,1,1,""]},"traits_futures.i_parallel_context.IParallelContext":{close:[10,3,1,""],closed:[10,3,1,""],event:[10,3,1,""],message_router:[10,3,1,""],worker_pool:[10,3,1,""]},"traits_futures.i_task_specification":{ITaskSpecification:[11,1,1,""]},"traits_futures.i_task_specification.ITaskSpecification":{background_task:[11,3,1,""],future:[11,3,1,""]},"traits_futures.multiprocessing_context":{MultiprocessingContext:[12,1,1,""]},"traits_futures.multiprocessing_context.MultiprocessingContext":{close:[12,3,1,""],closed:[12,3,1,""],event:[12,3,1,""],message_router:[12,3,1,""],worker_pool:[12,3,1,""]},"traits_futures.multiprocessing_router":{MultiprocessingReceiver:[13,1,1,""],MultiprocessingRouter:[13,1,1,""],MultiprocessingSender:[13,1,1,""],monitor_queue:[13,4,1,""]},"traits_futures.multiprocessing_router.MultiprocessingReceiver":{connection_id:[13,2,1,""],message:[13,2,1,""]},"traits_futures.multiprocessing_router.MultiprocessingRouter":{close_pipe:[13,3,1,""],manager:[13,2,1,""],pipe:[13,3,1,""],start:[13,3,1,""],stop:[13,3,1,""]},"traits_futures.multiprocessing_router.MultiprocessingSender":{send:[13,3,1,""],start:[13,3,1,""],stop:[13,3,1,""]},"traits_futures.multithreading_context":{MultithreadingContext:[14,1,1,""]},"traits_futures.multithreading_context.MultithreadingContext":{close:[14,3,1,""],closed:[14,3,1,""],event:[14,3,1,""],message_router:[14,3,1,""],worker_pool:[14,3,1,""]},"traits_futures.multithreading_router":{MultithreadingReceiver:[15,1,1,""],MultithreadingRouter:[15,1,1,""],MultithreadingSender:[15,1,1,""]},"traits_futures.multithreading_router.MultithreadingReceiver":{connection_id:[15,2,1,""],message:[15,2,1,""]},"traits_futures.multithreading_router.MultithreadingRouter":{close_pipe:[15,3,1,""],pipe:[15,3,1,""],start:[15,3,1,""],stop:[15,3,1,""]},"traits_futures.multithreading_router.MultithreadingSender":{send:[15,3,1,""],start:[15,3,1,""],stop:[15,3,1,""]},"traits_futures.null":{gui_test_assistant:[17,0,0,"-"],init:[18,0,0,"-"],pinger:[19,0,0,"-"]},"traits_futures.null.gui_test_assistant":{GuiTestAssistant:[17,1,1,""],TIMEOUT:[17,5,1,""]},"traits_futures.null.gui_test_assistant.GuiTestAssistant":{run_until:[17,3,1,""],setUp:[17,3,1,""],tearDown:[17,3,1,""]},"traits_futures.null.init":{toolkit_object:[18,5,1,""]},"traits_futures.null.pinger":{Pingee:[19,1,1,""],Pinger:[19,1,1,""]},"traits_futures.null.pinger.Pingee":{connect:[19,3,1,""],disconnect:[19,3,1,""]},"traits_futures.null.pinger.Pinger":{connect:[19,3,1,""],disconnect:[19,3,1,""],ping:[19,3,1,""]},"traits_futures.qt":{gui_test_assistant:[21,0,0,"-"],init:[22,0,0,"-"],pinger:[23,0,0,"-"]},"traits_futures.qt.gui_test_assistant":{GuiTestAssistant:[21,1,1,""],TIMEOUT:[21,5,1,""]},"traits_futures.qt.gui_test_assistant.GuiTestAssistant":{run_until:[21,3,1,""],setUp:[21,3,1,""],tearDown:[21,3,1,""]},"traits_futures.qt.init":{toolkit_object:[22,5,1,""]},"traits_futures.qt.pinger":{Pingee:[23,1,1,""],Pinger:[23,1,1,""]},"traits_futures.qt.pinger.Pingee":{connect:[23,3,1,""],disconnect:[23,3,1,""]},"traits_futures.qt.pinger.Pinger":{connect:[23,3,1,""],disconnect:[23,3,1,""],ping:[23,3,1,""]},"traits_futures.toolkit_support":{Toolkit:[24,1,1,""],toolkit:[24,5,1,""]},"traits_futures.toolkit_support.Toolkit":{toolkit_object:[24,3,1,""]},"traits_futures.traits_executor":{ExecutorState:[25,2,1,""],RUNNING:[25,5,1,""],STOPPED:[25,5,1,""],STOPPING:[25,5,1,""],TraitsExecutor:[25,1,1,""]},"traits_futures.traits_executor.TraitsExecutor":{running:[25,2,1,""],state:[25,2,1,""],stop:[25,3,1,""],stopped:[25,2,1,""],submit:[25,3,1,""],submit_call:[25,3,1,""],submit_iteration:[25,3,1,""],submit_progress:[25,3,1,""]},"traits_futures.version":{version:[26,5,1,""]},"traits_futures.wrappers":{BackgroundTaskWrapper:[27,1,1,""],CONTROL:[27,5,1,""],CUSTOM:[27,5,1,""],FutureWrapper:[27,1,1,""],RAISED:[27,5,1,""],RETURNED:[27,5,1,""],STARTED:[27,5,1,""]},"traits_futures.wrappers.BackgroundTaskWrapper":{send_control_message:[27,3,1,""],send_custom_message:[27,3,1,""]},"traits_futures.wrappers.FutureWrapper":{done:[27,2,1,""],future:[27,2,1,""],receiver:[27,2,1,""]},"traits_futures.wx":{gui_test_assistant:[29,0,0,"-"],init:[30,0,0,"-"],pinger:[31,0,0,"-"]},"traits_futures.wx.gui_test_assistant":{AppForTesting:[29,1,1,""],GuiTestAssistant:[29,1,1,""],TIMEOUT:[29,5,1,""],TimeoutTimer:[29,1,1,""]},"traits_futures.wx.gui_test_assistant.AppForTesting":{OnInit:[29,3,1,""],close:[29,3,1,""],exit:[29,3,1,""]},"traits_futures.wx.gui_test_assistant.GuiTestAssistant":{run_until:[29,3,1,""],setUp:[29,3,1,""],tearDown:[29,3,1,""]},"traits_futures.wx.gui_test_assistant.TimeoutTimer":{Notify:[29,3,1,""],start:[29,3,1,""],stop:[29,3,1,""]},"traits_futures.wx.init":{toolkit_object:[30,5,1,""]},"traits_futures.wx.pinger":{Pingee:[31,1,1,""],Pinger:[31,1,1,""]},"traits_futures.wx.pinger.Pingee":{connect:[31,3,1,""],disconnect:[31,3,1,""]},"traits_futures.wx.pinger.Pinger":{connect:[31,3,1,""],disconnect:[31,3,1,""],ping:[31,3,1,""]},traits_futures:{"null":[16,0,0,"-"],api:[1,0,0,"-"],background_call:[2,0,0,"-"],background_iteration:[3,0,0,"-"],background_progress:[4,0,0,"-"],base_future:[5,0,0,"-"],exception_handling:[6,0,0,"-"],future_states:[7,0,0,"-"],i_future:[8,0,0,"-"],i_message_router:[9,0,0,"-"],i_parallel_context:[10,0,0,"-"],i_task_specification:[11,0,0,"-"],multiprocessing_context:[12,0,0,"-"],multiprocessing_router:[13,0,0,"-"],multithreading_context:[14,0,0,"-"],multithreading_router:[15,0,0,"-"],qt:[20,0,0,"-"],toolkit_support:[24,0,0,"-"],traits_executor:[25,0,0,"-"],version:[26,0,0,"-"],wrappers:[27,0,0,"-"],wx:[28,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","method","Python method"],"4":["py","function","Python function"],"5":["py","data","Python data"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:method","4":"py:function","5":"py:data"},terms:{"100":33,"10101":34,"2018":[32,33,35,36],"2021":[32,33,35,36],"243":35,"50th":33,"\u03c0":36,"abstract":[8,9,10,11],"boolean":[17,21,29,32,36],"case":[13,15,25,32,34],"class":[1,2,3,4,5,7,8,9,10,11,12,13,14,15,17,18,19,21,22,23,24,25,27,29,30,31,32,33,34,35,36],"default":[8,9,17,21,25,29,32,34],"enum":[7,25],"export":1,"final":[7,33,34],"float":[17,21,29],"function":[0,2,3,4,5,8,19,23,25,31,32,33,34,36],"import":[1,32,33,34,35,36],"int":[10,12,13,14,15,25,32,33,34,36],"long":[13,35,36],"new":[9,12,13,14,15,25,33,34,35,36],"null":[0,36],"public":1,"return":[2,3,4,5,8,9,10,11,12,13,14,15,17,21,25,27,29,32,33,34,36],"throw":33,"true":[5,8,10,11,12,14,17,21,25,29,32,33,34,36],"while":[9,11,13,15,32,36],Adding:33,But:33,For:[13,32,33,34,35],Its:34,Not:[9,13,15],One:[5,8],That:[33,34],The:[2,3,4,5,8,9,10,11,13,15,17,18,19,21,22,23,24,25,27,29,30,31,33,34,35,36],These:[4,25,27],Use:[25,33],Using:36,With:32,__main__:[32,33],__name__:[32,33],_cancel_running_task:32,_get_can_calcul:[32,33],_get_can_cancel:[32,33],_get_no_running_futur:36,_local_message_queu:13,_monitor_thread:13,_process_:32,_process_buzz:32,_process_fizz:32,_process_fizz_buzz:32,_process_message_queu:13,_record_result:34,_report_buzz:32,_report_fizz:32,_report_fizz_buzz:32,_report_partial_result:33,_report_progress:34,_report_result:[33,36],_request_cancel:33,_reset_futur:32,_route_messag:13,_submit_background_cal:36,_submit_calcul:[32,33],_task_sent:32,_update_result:34,abc:[2,3,4,10,11,27,32],abil:[17,21,29,33],abort:34,about:[5,8,33,34,36],abov:[32,33,34,35],abstractcontextmanag:9,accept:[2,3,4,25,32,34],access:[5,8,24,34,36],accompani:32,accur:36,acknowledg:34,across:6,actual:[2,9,35],adapt:[8,9],adaptation_error:[8,9],adaptationerror:[8,9],adapte:[8,9],add:33,addit:[4,27,33,34],advanc:36,advis:34,aforement:[32,33,35,36],after:[9,13,15,19,23,31,32,33,34,35],again:35,alert:13,algorithm:33,alia:25,all:[9,13,15,27,33,34,35,36],alloc:9,allow:[13,15,17,21,29,32,33,34],alreadi:[5,8,9,13,15,19,23,29,31,33,34],also:[4,9,13,32,33,34,35,36],alwai:[5,8,9,13,15,27],ani:[5,8,9,10,11,12,13,14,15,19,23,27,29,31,32,33,34],anoth:34,anyth:32,apart:33,api:[0,10,32,33,34,35],app:29,append:34,appfortest:29,appli:27,applic:[29,33,34,36],appropri:[9,25],approxim:36,approximate_pi:33,arbitrari:[4,17,21,25,29,34],arg:[2,3,4,23,25,29,31],argument:[2,3,4,11,17,19,21,23,25,27,29,31,32,34],around:[2,24,33],arriv:[3,4,9,13,32,34,36],assertequ:35,asserteventuallytrueingui:35,assign:33,associ:34,assum:[13,25,34],asynchron:34,asyncio:19,attempt:[5,8,34],attribut:[5,8,32,33,34],attributeerror:[5,8,34],austin:[32,33,35,36],avail:[5,8,32,33,34,35,36],avoid:35,await:7,back:[11,13,15],backend:24,background:[0,2,3,4,5,6,7,8,9,11,13,15,19,23,25,27,31,33,35],background_cal:[0,36],background_iter:[0,36],background_progress:[0,36],background_task:[2,3,4,11,27,32],backgroundcal:[2,11],backgroundfizzbuzz:32,backgrounditer:[3,11],backgroundprogress:4,backgroundtaskwrapp:27,base:[2,3,4,5,8,9,10,11,12,13,14,15,17,19,21,23,24,25,27,29,31,32,34,36],base_futur:[0,2,3,4,36],base_toolkit:[18,22,30],basefutur:[1,2,3,4,5,8,32],basic:[32,33],becaus:[34,35],been:[2,3,4,5,7,8,9,11,13,15,25,27,32,34],befor:[9,10,12,13,14,15,17,19,21,23,27,29,31,33,34],behaviour:33,being:[27,35],below:32,best:[5,8,34],between:[9,13],bit:34,block:35,bool:[5,8,25,27,32,33,36],both:[11,25,33],boundari:6,brief:[33,34],bsd:[32,33,35,36],busi:34,button:[32,33,36],buzz:36,calcul:[32,33,34,36],call:[2,3,4,9,11,13,15,17,19,21,23,25,27,29,31,32,33,34,35,36],callabl:[2,3,4,11,17,19,21,23,25,27,29,31,33,34,36],callback:[13,19,23,29,31],callbackgroundtask:2,callfutur:[1,2,25,33,34,36],can:[2,3,4,5,6,8,9,10,11,12,13,14,15,19,23,25,27,29,31,32,33,34,35,36],can_calcul:[32,33],can_cancel:[32,33],cancel:[1,2,3,4,5,7,8,11,25,27,32,35,36],cancel_ev:27,cancellable_st:7,cannot:34,carlo:33,carri:33,caus:34,challeng:35,chang:[5,8,17,21,27,29,33,34,36],channel:9,check:[2,3,4,11,27,32,33,35],child:13,choic:[12,14,25],choos:[10,32,34],chunk:34,circl:33,clean:29,cleaner:32,cleanup:[10,12,14],close:[9,10,12,13,14,15,29],close_pip:[9,13,15],code:[4,29,32,33,36],collect:[2,3,4,27,32],com:[32,33,35,36],come:32,common:5,commun:[4,5,8,9,13,15,27,32,35],compar:33,compat:25,complet:[1,5,7,8,25,27,29,33,34,35,36],compon:34,compound:34,comput:[33,34,35,36],concurr:[2,10,12,14,25,34,36],condit:[17,21,29,32,33,35,36],configure_trait:[32,33,36],connect:[9,13,15,19,23,31],connection_id:[13,15],consist:[2,5,8,34],constant:[1,5,8,11,32],consum:11,contain:[1,5,8,11,27,33,34],content:4,context:[0,10,12,14,25,36],contextlib:9,continu:13,control:27,conveni:[2,3,4,5,25,32,34],convers:33,cooper:[33,36],copi:36,copyright:[32,33,35,36],core:[1,10],correspond:[4,11,25,32,33,34],could:33,count:[32,33],coupl:32,cours:34,creat:[9,11,13,15,25,34,36],creator:25,cross:[19,23,31,36],crude:33,current:[9,13,15,24,25,32,34,35,36],current_step:34,custom:[8,27,32],dai:36,data:34,deadlock:36,deal:[11,34],decid:36,dedic:32,def:[32,33,34,35,36],defin:[0,32,36],deleg:[12,14,25,27],deliv:35,demonstr:[32,33],depend:[10,34],depends_on:[32,33,36],deprec:25,deriv:[25,34],describ:[11,32,33,34,35,36],design:[35,36],desktop:33,detail:[6,9,32,33,34],determin:13,dev0:[26,36],diagram:34,dict:[2,3,4,29,34],dictionari:29,differ:[32,34],directli:[32,34],discard:9,disconnect:[19,23,31],dispatch:[9,32,36],dispos:[9,10,12,14,25],doe:[4,32,33,35],doesn:[33,34],don:[32,33,35],done:[5,8,27,32,33,34,35,36],done_st:7,down:[25,34,35],dure:[32,33,34],each:[8,13,32,33,34,35],easi:[33,35],easili:36,effect:[9,35],either:[5,11,34],elif:[32,33],elimin:36,els:[5,8,10,12,14,33],emitt:[19,23,31],enabl:[32,33,36],enabled_when:[32,33,36],encapsul:32,encount:33,end:[2,4,9,13,15,32,33,34,35],ensur:[9,29],enthought:[32,33,35,36],entri:[18,22,30,34],error:[7,33,34],evalu:[17,21,29],even:34,event:[3,4,8,9,10,12,13,14,15,17,21,29,32,33,34,35,36],eventu:[4,33,34,35],ever:33,everi:[4,17,19,21,23,29,31,33],everyth:[1,32],exactli:[5,8,34],examin:34,exampl:[10,25,34,36],exc_info:[5,8],except:[5,6,7,8,11,17,21,27,29,32,33,34],exception_handl:[0,36],exclus:25,execut:[1,2,3,4,5,7,8,11,13,15,19,23,25,29,31,32,33,34,35],executor:[0,2,3,4,8,10,12,14,25,27,32,33,35,36],executorst:[1,25,34],exist:[25,34],exit:[29,34],exit_cod:29,expect:[19,23,31,32,33,34,35],expert:36,expir:29,explicitli:34,express:33,extend:36,face:35,facil:36,fact:34,factori:32,fail:[1,5,7,8,33,34,35],failur:34,fals:[5,8,10,11,12,14,25,27,32],far:34,find:[18,22,30,35],finish:[9,13,15,34],fire:[3,4,5,8,9,13,15,32,36],first:[24,32],fix:[19,23,24,31],fizz:36,fizz_buzz:32,fizz_buzz_task:32,fizzbuzzfutur:32,fizzbuzzui:32,flavour:[5,9],follow:[1,13,33,34],foreground:[3,9,11,13,15,27,36],forev:35,form:[5,8,10,11,33,34],format:[5,8,32,34,36],fortun:33,friendli:[12,14],from:[1,3,4,5,6,7,8,9,10,13,15,17,19,21,23,27,29,31,32,33,34,35,36],front:[2,4,32],fulli:35,further:[5,8,33,34],futur:[0,2,3,4,5,7,8,9,10,11,12,14,25,27,33],future_st:[0,36],futurest:[1,5,7,8,34],futurewrapp:27,game:32,gener:[3,32,33],get:[32,33,36],give:[4,32,34,35],given:[3,9,10,12,14,17,19,21,23,25,27,29,31,32,34,36],goe:33,guarante:1,gui:[9,13,15,33,35,36],gui_test_assist:[0,16,20,28,35,36],guid:[33,34],guitestassist:[17,21,29,35],half:[9,13,15],handl:[2,4,27,32],handler:32,hang:35,happen:34,has:[2,3,4,5,7,8,9,11,13,15,25,27,32,33,34,35],has_trait:[2,3,4,5,8,9,13,15,17,21,25,27,29],hasn:29,hasrequiredtrait:13,hasstricttrait:[2,3,4,5,13,15,25,27,32,33,36],hastrait:[17,21,27,29,36],have:[10,11,29,32,34,35],here:[11,32,33,34,35,36],hgroup:[32,33],high:33,hint:35,hit:35,hold:[17,21,29],hook:34,how:[11,32,33,34],howev:[33,34],http:[32,33,35,36],i_futur:[0,36],i_message_rout:[0,36],i_parallel_context:[0,12,14,36],i_task_specif:[0,36],ideal:[4,32,33],identifi:32,ifutur:[1,8,11,25,27,32,33],illustr:33,imessagereceiv:[9,13,15],imessagerout:[9,10,13,15],imessagesend:[9,13,15,27],immedi:[5,8,13,34,36],immut:[4,9,11,13,15,32,33],implement:[0,9,10,11,15,32,33,36],impli:34,inc:[32,33,35,36],includ:[4,25,32,33,34,35,36],incom:[13,36],increas:33,index:36,indic:[11,27],ineffici:33,inform:[4,5,6,8,26,27,33,34,36],ingredi:32,inherit:32,init:[0,16,20,28,36],initi:[25,34],input:[17,21,29,36],input_for_calcul:36,insert:33,insid:33,inspect:13,instal:35,instanc:[9,13,15,27,32,33,34,36],instanti:[13,15,34],instead:[5,8,25,33,34,35],integ:[32,34],integr:36,intend:32,interact:[35,36],interest:[34,35],interfac:[8,9,10,11,13,15,32],interpret:[4,8,34],interrog:32,interrupt:[34,36],interruptible_sum_of_squar:34,interruptible_task:33,interruptibletaskexampl:33,interv:34,introduc:34,introduct:36,invok:11,iparallelcontext:[1,10,12,14,25],ipinge:[13,15],is_set:10,isn:32,issu:36,itaskspecif:[1,11,25,32],item:[33,34,36],iter:[3,25,32,33,34,36],iterationbackgroundtask:3,iterationfutur:[1,3,25,33,34],its:[5,9,13,32,33,34,35,36],itself:35,job:[9,11,25,32,34,35],just:33,keep:[35,36],kei:34,kept:[9,13,15],keyword:29,know:11,knowledg:[5,8,34],known:32,kwarg:[2,3,4,23,25,29,31],lambda:35,land:33,laptop:33,larg:[34,36],last:[32,36],latenc:33,later:[32,36],layer:9,leak:35,least:[29,32],leav:36,length:34,level:34,librari:1,licens:[32,33,35,36],like:[8,10,12,14,25,32,33,34],line:33,link:[4,9,19,23,31],listen:[5,8,9,13,33,34],littl:34,local:13,local_queu:13,log:[9,13,15,33],logic:10,longer:[19,23,25,29,31,34],look:[32,34],loop:[9,13,17,21,29,35,36],machin:[10,33],machineri:[5,13,27,34],made:[1,9,13,15,19,23,31,32],mai:[4,11,32,33,34,35,36],main:[9,11,13,15,19,23,29,31,34,35,36],make:[32,35,36],manag:[13,25],manner:[19,23,31],mark:4,marshal_except:6,match:[13,15,34],max_step:34,max_work:[10,12,14,25,34],maximum:[10,12,14,25,35],mayb:36,mean:[9,33,34,35,36],mechan:32,meet:32,mention:[33,34],messag:[2,3,4,7,8,9,10,11,12,13,14,15,27,33,34,36],message_arg:[8,11,27],message_argu:32,message_queu:[13,15],message_rout:[10,12,14],message_typ:[8,11,27,32],method:[9,10,13,15,19,23,25,31,32,33,34,35],mid:33,might:34,minim:36,minimum:10,modif:33,modifi:33,modul:[0,16,20,28,34,36],monitor:[2,3,4,11,13,17,21,29,32,34],monitor_queu:13,mont:33,more:[7,9,13,15,33,34],most:32,move:[5,8,13,33,34],multipl:[32,34],multiprocess:[10,12,13,25,36],multiprocessing_context:[0,36],multiprocessing_rout:[0,36],multiprocessingcontext:12,multiprocessingreceiv:13,multiprocessingrout:[12,13],multiprocessingsend:13,multithread:[10,14,25,34],multithreading_context:[0,36],multithreading_rout:[0,36],multithreadingcontext:[1,14],multithreadingreceiv:15,multithreadingrout:[14,15],multithreadingsend:15,must:[4,9,13,15,19,23,25,31,32,33,34,35],mutat:32,mutual:25,my_executor:34,my_result:34,n_is_multiple_of_3:32,n_is_multiple_of_5:32,name:[2,3,4,17,21,25,29,32,34,36],necessari:[9,10,12,13,14,15,32],necessarili:34,need:[1,9,10,25,29,32,33,34,35,36],never:[34,35],next:[9,13,32,34],no_running_futur:36,non_interruptible_task:33,none:[10,12,13,14,25,27,32,33,36],noninterruptibletaskexampl:33,note:[11,25,32,33,35],noth:32,notifi:[13,15,29],now:[32,33],number:[10,12,14,17,21,25,29,32,33],object:[2,3,4,5,8,9,11,13,15,17,18,19,21,22,23,24,25,27,29,30,31,32,33,36],oblig:11,observ:[32,33],obtain:[5,8],occur:[5,8,13,33,34,35],off:36,often:33,old:25,on_p:[13,19,23,31],on_trait_chang:[34,36],onc:[5,8,25,33,34],one:[5,7,8,29,33,34,35,36],ones:25,ongo:33,oninit:29,onli:[5,8,9,17,21,29,32,33,34,35,36],onlin:[32,33,35,36],onto:13,open:[32,33,35,36],oper:32,option:[10,11,12,14,17,21,25,27,29,32],order:[9,33,34,35,36],origin:33,other:[1,4,10,11,32,36],otherwis:32,our:[32,35],out:[17,21,29,33],overrid:29,overridden:32,overview:[0,36],own:[13,34,36],ownership:9,packag:[1,26,34,36],page:36,pair:[9,13,15,34],parallel:[0,10,25,36],paramet:[2,3,4,9,10,12,13,14,15,17,19,21,23,25,27,29,31,32,34],parameterless:[19,23,31],part:32,partial:36,particular:[10,11,35],pass:[2,3,4,9,13,15,25,27,29,32,34],pattern:36,payload:[32,33],pend:[13,15],per:33,perform:35,perhap:10,permit:[7,9,13,15],pickleabl:[4,9,11,13,15,32,33],piec:[5,32],ping:[13,15,19,23,31],pinge:[13,15,19,23,31],pinger:[0,16,20,28,36],pipe:[9,13,15],place:[13,32],plain:33,platform:36,player:34,plu:[32,33],point:[4,5,8,17,18,21,22,29,30,33,34,35],pool:[4,10,12,14,25,36],portion:4,posit:[2,3,4,25,29,32,34],possibl:[32,33,34],potenti:[35,36],pow:35,prefer:32,prefix:27,prepar:[9,13,15,19,23,31],present:[10,36],press:[33,36],prevent:[25,35],previou:[33,36],previous:[9,13,15,34],primit:[10,25],privat:[25,32],process:[6,9,13,27,32,34],process_queu:13,processpoolexecutor:12,produc:[9,13,15,34],progress:[4,25,32,33,34,36],progress_info:[4,34],progressbackgroundtask:4,progressfutur:[1,4,25,34],progressreport:4,properti:[5,8,10,12,14,24,25,32,33,34,36],proport:33,provid:[2,4,5,8,9,10,12,14,17,19,21,23,24,25,27,29,31,32,33,34,35,36],proxi:13,pull:13,purpos:34,put:[13,34,36],pyfac:[18,22,23,30,35],pyqt:35,pysid:35,python:[11,25,32,33,34,36],qt4:35,qtcore:23,quarter:33,queu:7,queue:[9,13,15],quickstartexampl:36,race:36,rais:[5,7,8,9,11,13,15,17,21,27,29,32,33,34],random:33,rang:[33,34],rare:33,rather:[33,35],reach:[5,8,9,13,15,17,21,29,34,35],react:[9,13,15],readi:32,readonli:[32,33,36],real:24,reason:33,receiv:[7,9,13,15,19,23,27,31,32,34,35],recipi:[13,15],record:[11,27,34,36],redistribut:[32,33,35,36],refer:33,regardless:[17,21,29],regist:32,relat:[25,34],releas:36,reli:35,remain:[9,13,15,33],remov:[9,13,15,35],replac:33,report:[4,25,32,34,36],repres:[1,2,3,4,7,25,27,32,33,34],represent:3,request:[2,3,4,5,7,8,9,11,19,23,25,27,31,32,33,34,35],requir:36,reserv:[32,33,35,36],resiz:[32,33,36],resourc:[9,18,22,25,30],respect:32,respond:36,respons:[7,9,25,33,34,36],rest:35,restart:34,result:[3,5,8,11,27,32,35,36],result_ev:[3,33,34],retriev:34,right:[32,33,35,36],rout:[9,13,15],router:[9,10,12,13,14,15],run:[1,2,9,13,15,17,21,25,29,32,33,34,35,36],run_until:[17,21,29],runtimeerror:[5,8,9,13,15,17,21,29,33,34],safe:[5,6,8,9,10,12,13,14,15,19,23,25,31,32,33,35],safety_timeout:35,same:[9,10,13,15,34],sample_count:33,schedul:[34,35],search:36,second:[17,21,29,32,33,35],section:[32,33,34,35],see:[32,34],self:[13,32,33,34,35,36],send:[2,3,4,9,11,13,15,19,23,27,31,32,34,36],send_control_messag:27,send_custom_messag:27,sender:[9,13,15,27],sent:[3,4,9,13,15,19,23,27,31,32,34],sequenc:34,server:13,set:[10,13],setup:[9,13,15,17,21,29,35],sever:[29,33],share:[10,12,13,14,36],shareabl:[10,12,14],shot:29,should:[1,3,4,9,10,11,13,15,19,23,25,31,32,33,34,35],shouldn:33,show:[32,34,36],shut:[25,34,35],shutdown:34,side:35,signatur:11,similarli:32,simpl:[2,11,32,33,34,35,36],simplist:33,sinc:[25,32],singl:[4,9,11,17,21,29,34],six:[5,8,34],sleep:[32,36],slow_squar:36,slowli:[32,33,36],small:[9,13,15],smaller:34,softwar:[32,33,35,36],solut:36,some:[9,32,33,34,35],someth:[3,6,33],somewhat:[17,21,29],sourc:[2,3,4,5,6,8,9,10,11,12,13,14,15,17,19,21,23,24,25,27,29,31,32,33,35,36],space:33,specif:[2,3,4,11,18,22,24,30,36],specifi:11,squar:[33,34,36],stabil:1,standard:32,start:[9,13,15,27,29,33,34],state:[0,2,3,4,5,7,8,25,27,32,33,35,36],statement:33,statu:[2,3,4,11,32],step:[13,34],steps_complet:34,still:[5,8,33,34],stop:[1,9,13,15,25,29,35,36],store:34,str:[2,3,4,5,8,17,21,27,29,32,33,36],strictli:32,string:[5,8,11,26,32],stringifi:34,structur:9,style:[32,33,36],subclass:[8,29,32],submiss:[0,4,32,33,34,36],submit:[2,3,4,11,25,27,33,35,36],submit_cal:[1,2,25,32,33,34,35,36],submit_fizz_buzz:32,submit_iter:[1,3,25,32,33,34],submit_progress:[1,4,25,32,34],subpackag:1,succeed:27,success:35,successfulli:34,suit:35,suitabl:[10,12,14,32,36],sum:34,suppli:[25,33],support:[0,4,6,17,21,24,29,36],suppress:32,tabl:[9,13,15],take:[8,9,29,33,34],target:[4,10,19,23,27,31],task:[0,2,3,4,5,6,7,8,9,11,13,15,25,27,35,36],teardown:[9,13,15,17,21,29,35],tell:34,term:[32,33,35,36],test:[17,21,29,33,36],test_my_futur:35,testcas:35,testmyfutur:35,than:[4,33,34,35],thank:[32,33,35,36],thei:[8,25,34],them:34,thi:[1,2,3,4,5,8,9,10,11,12,13,14,15,17,19,21,23,24,25,27,29,31,32,33,34,35,36],thing:32,those:[13,32,33,35],though:[32,33],thousand:33,thread:[6,9,10,11,13,15,19,23,31,34,35,36],thread_pool:25,threadpoolexecutor:[14,34],three:[32,34],time:[17,19,21,23,24,29,31,32,33,34,36],timeout:[17,21,29,35],timeouttim:29,timer:29,tip:35,togeth:36,too:33,toolkit:[18,22,24,30,35],toolkit_object:[18,22,24,30,35],toolkit_support:[0,36],top:34,topic:[34,36],total:[33,34],total_step:34,traceback:[5,8,34],tradit:36,trait:[1,2,3,4,5,7,8,9,13,15,17,21,25,27,29,32,33,34],traits_executor:[0,36],traits_futur:[32,33,34,35,36],traits_view:[32,33,36],traitsexecutor:[1,2,3,4,10,11,12,14,25,27,32,33,34,35,36],traitsui:[32,33],transfer:[6,13],transit:34,transmit:6,tupl:[2,3,4,5,8,27,29,34],turn:[6,33],two:[32,33,34,35],txt:[32,33,35,36],type:[0,2,3,4,5,7,8,10,11,12,14,25,27,33,34,36],typic:[9,11,13,15,33,35],uitem:[32,33,36],unclos:[9,13,15],under:[32,33,35,36],underli:[25,27,34],understand:34,undo:[9,19,23,31],unexpect:33,unilater:33,unit:[29,33,35],unittest:35,unlik:36,until:[17,19,21,23,29,31,33,35],updat:[34,36],update_plot_data:34,usabl:33,use:[2,3,4,10,12,13,14,19,23,25,31,32,33,34,35],used:[2,3,4,7,9,11,13,15,18,22,24,27,29,30,32,33,34,36],useful:[11,33],user:[0,33,34],uses:[13,32,33,35],using:[9,13,15,19,23,31,32,33,34,35,36],usual:[9,32],util:35,valid:32,valu:[5,8,34],variou:[5,7,34],veri:33,version:[0,25,33,34,36],via:[9,13,32,33,34],view:[32,33,36],wai:[8,19,23,31,32,33,34,35],wait:[1,5,7,8,25,34,35],want:[32,33,34,35],warn:[9,13,15],warranti:[32,33,35,36],well:[32,34],whatev:[8,32,33],when:[3,5,8,9,11,13,15,19,23,27,29,31,33,34,36],whenev:[3,4,13,19,23,31,32,33],where:[4,9,13,15,34],whether:[2,3,4,11,17,21,27,29,32,36],which:[7,9,13,15,19,23,25,31,32,33,34,36],whose:[17,21,29,34],window:29,wish:9,without:[5,7,8,32,33,34,35,36],won:[34,35],work:[33,36],worker:[4,10,12,13,14,15,25,36],worker_pool:[10,12,14,25,34],would:33,wrap:27,wrapper:[0,2,24,36],write:32,www:[32,33,35,36],wxpython:[31,35],yet:[34,36],yield:[3,33],you:[1,32,33,34,35],your:[33,34,36],zero:[19,23,27,31,32]},titles:["traits_futures package","traits_futures.api module","traits_futures.background_call module","traits_futures.background_iteration module","traits_futures.background_progress module","traits_futures.base_future module","traits_futures.exception_handling module","traits_futures.future_states module","traits_futures.i_future module","traits_futures.i_message_router module","traits_futures.i_parallel_context module","traits_futures.i_task_specification module","traits_futures.multiprocessing_context module","traits_futures.multiprocessing_router module","traits_futures.multithreading_context module","traits_futures.multithreading_router module","traits_futures.null package","traits_futures.null.gui_test_assistant module","traits_futures.null.init module","traits_futures.null.pinger module","traits_futures.qt package","traits_futures.qt.gui_test_assistant module","traits_futures.qt.init module","traits_futures.qt.pinger module","traits_futures.toolkit_support module","traits_futures.traits_executor module","traits_futures.version module","traits_futures.wrappers module","traits_futures.wx package","traits_futures.wx.gui_test_assistant module","traits_futures.wx.init module","traits_futures.wx.pinger module","Advanced topics","Making tasks interruptible","Introduction","Testing Traits Futures code","Traits Futures: reactive background processing for Traits and TraitsUI"],titleterms:{"\u03c0":33,"function":1,"new":32,"null":[16,17,18,19],The:32,Using:34,advanc:32,all:32,api:[1,9,36],approxim:33,background:[1,32,34,36],background_cal:2,background_iter:3,background_progress:4,base_futur:5,buzz:32,callabl:32,cancel:[33,34],code:35,context:1,creat:32,defin:1,document:36,exampl:[32,33,35],exception_handl:6,executor:[1,34],featur:36,fizz:32,foreground:32,futur:[1,32,34,35,36],future_st:7,get:34,gui:32,gui_test_assist:[17,21,29],guid:36,i_futur:8,i_message_rout:9,i_parallel_context:10,i_task_specif:11,implement:13,indic:36,init:[18,22,30],interrupt:33,introduct:34,limit:36,make:33,messag:32,modul:[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,21,22,23,24,25,26,27,29,30,31],multiprocessing_context:12,multiprocessing_rout:13,multithreading_context:14,multithreading_rout:15,object:34,overview:[9,13],own:32,packag:[0,16,20,28],parallel:1,partial:33,pinger:[19,23,31],pool:34,process:36,put:32,quick:36,reactiv:36,result:[33,34],send:33,share:34,specif:32,start:36,state:[1,34],stop:34,submiss:1,submit:[32,34],support:1,tabl:36,task:[1,32,33,34],test:35,togeth:32,toolkit_support:24,topic:32,trait:[35,36],traits_executor:25,traits_futur:[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],traitsui:36,type:[1,32],user:[1,36],version:26,work:[32,34],worker:34,wrapper:27,your:32}})