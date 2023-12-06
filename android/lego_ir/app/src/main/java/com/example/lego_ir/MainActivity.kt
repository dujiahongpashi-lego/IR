package com.example.lego_ir

import android.hardware.ConsumerIrManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.ImageView
import androidx.appcompat.app.AppCompatActivity
import com.bumptech.glide.Glide

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val kafkaGif: ImageView = findViewById(R.id.imageViewBiliGif)
        //kafkaGif.setRotation(90F)
        Glide.with(this)
            .load(R.drawable.yjsl_v_v_speed)
            .into(kafkaGif)
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.v("bt", "onDestroy")
    }

    override fun onStop() {
        super.onStop()
        Log.v("bt", "onStop")
//        val CODE_ARRAY = intArrayOf(
//            65, 65, 65, 65, 65, 65
//        )
        val CODE_ARRAY = intArrayOf(
            65, 65, 65, 65, 65, 65
        )
        transmitIR_ORIGEN(CODE_ARRAY)
    }

    fun onPress(view: View) {
        Log.v("bt", "Press")
        val CODE_ARRAY = intArrayOf(
            71, 71, 71, 71, 71, 71
        )
        transmitIR_ORIGEN(CODE_ARRAY)
    }

    private fun transmitIR_ORIGEN(code: IntArray): String {
        val mCIR = getSystemService(CONSUMER_IR_SERVICE) as ConsumerIrManager
        if(!mCIR.hasIrEmitter()) {
            return "手机红外初始化失败，须用真机"
        }
        return "OK" + sendCode(mCIR, code)
    }

    private fun transmitIR(code: IntArray): String {
        val mCIR = getSystemService(CONSUMER_IR_SERVICE) as ConsumerIrManager
        if(!mCIR.hasIrEmitter()) {
            return "手机红外初始化失败，须用真机"
        }
//        return "OK" + sendCode(mCIR, code)
        mCIR.transmit(38000, code)
        return "OK"
    }

    // 低电平
    val LOW = 540

    // 高电平0
    val HIGH0 = 540

    // 高电平1
    val HIGH1 = 1620

    // 引导码
    val START_L = 4400
    val START_H = 4400

    // 分隔符S
    val S_L = 540
    val S_H = 5220

    // 一次发送终止符
    val END_L = 560
    val END_H = 20000

    // 频率
    val frequency = 38000

    // 关机QQ'YY'
    val QY = intArrayOf(
        0, 255, 0, 255
    )

    // 将二进制数组转换为红外线信号数组
    fun binaries2Irs(binaries: IntArray): IntArray {
        val ans = IntArray(binaries.size * 2)
        var i: Int
        i = 0
        while (i < binaries.size) {
            when (binaries[i]) {
                0 -> {
                    ans[i * 2] = LOW
                    ans[i * 2 + 1] = HIGH0
                }

                1 -> {
                    ans[i * 2] = LOW
                    ans[i * 2 + 1] = HIGH1
                }
            }
            i++
        }
        return ans
    }

    // 8位转二进制数组
    fun ints2binaries(ints: IntArray): IntArray {
        val binaries = IntArray(ints.size * 8)
        var i: Int
        var j: Int
        var mid: Int
        i = 0
        while (i < ints.size) {
            mid = ints[i]
            j = 0
            while (j < 8) {
                binaries[i * 8 + j] = mid shr 7 - j and 0x1
                j++
            }
            i++
        }
        return binaries
    }

    // 控制空调状态
    fun send(manager: ConsumerIrManager, array: IntArray, isOpen: Boolean): IntArray? {
        // 获取最终发送码
        val binaries: IntArray = ints2binaries(array)
        val irs: IntArray = binaries2Irs(binaries)
        val ans: IntArray
        ans = if(isOpen) {
            IntArray(2 + irs.size + 2 + 2 + irs.size + 2)
        } else {
            IntArray(2 + irs.size + 2 + 2 + irs.size + 2 + 2 + irs.size + 2)
        }
        ans[0] = START_L
        ans[1] = START_H
        var i: Int
        var j: Int
        var k: Int
        i = 0
        while (i < irs.size) {
            ans[2 + i] = irs[i]
            i++
        }
        // 分隔码S
        ans[irs.size + 2] = S_L
        ans[irs.size + 3] = S_H
        // 重复第二帧
        ans[irs.size + 4] = START_L
        ans[irs.size + 5] = START_H
        i = 0
        while (i < irs.size) {
            ans[irs.size + 6 + i] = irs[i]
            i++
        }
        // 如果是开机控制，则加入结束码即可
        if(isOpen) {
            // 再加入结束码
            ans[2 + irs.size + 2 + 2 + irs.size] = END_L
            ans[2 + irs.size + 2 + 2 + irs.size + 1] = END_H
        } else {
            // 加入关机特殊码:S,L,A,A',Q,Q',Y,Y',END
            // 直接关机的话，Q与Y的八位全是0
            i = 2 + irs.size + 2 + 2 + irs.size
            while (i < 2 + irs.size + 2 + 2 + irs.size + 2 + 2 + 32) {
                ans[i] = ans[i - (2 + 2 + irs.size)]
                i++
            }
            // 获取QQ'YY'的Irs时间长度码数组
            val QQYY: IntArray = binaries2Irs(ints2binaries(QY))
            while (i < 2 + irs.size + 2 + 2 + irs.size + 2 + 2 + 32 + QQYY.size) {
                ans[i] = QQYY[i - (2 + irs.size + 2 + 2 + irs.size + 2 + 2 + 32)]
                i++
            }
            // 加入结束码
            ans[i] = END_L
            i++
            ans[i] = END_H
        }

        // 最终发送码获取完成，开始发送
        if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            manager.transmit(frequency, ans)
        }
        return ans
    }

    fun sendCode(mConsumerIrManager: ConsumerIrManager, code: IntArray): IntArray? {
        return send(mConsumerIrManager, code, false)
    }
}