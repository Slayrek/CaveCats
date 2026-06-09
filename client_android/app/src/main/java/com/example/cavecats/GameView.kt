package com.example.cavecats

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.SurfaceHolder
import android.view.SurfaceView
import org.json.JSONArray
import org.json.JSONObject

class GameView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null, defStyleAttr: Int = 0
) : SurfaceView(context, attrs, defStyleAttr), SurfaceHolder.Callback, Runnable {

    private var thread: Thread? = null
    private var isRunning = false
    val networkClient = NetworkClient()
    
    private val paint = Paint()
    private var bitmaps = mutableMapOf<String, Bitmap>()
    
    // Game State
    private var playerX = 0f
    private var playerY = 0f
    private var mobsData: JSONArray? = null
    
    // Joystick/Buttons
    private val btnLeft = Rect()
    private val btnRight = Rect()
    private val btnJump = Rect()
    private val btnAction = Rect()

    init {
        holder.addCallback(this)
        loadAssets()
        
        networkClient.onEntitySyncReceived = { obj ->
            // Parse entities
            val mobs = obj.optJSONArray("mobs")
            if (mobs != null) {
                mobsData = mobs
            }
        }
    }

    private fun loadAssets() {
        try {
            val am = context.assets
            bitmaps["cat"] = BitmapFactory.decodeStream(am.open("pics/cat1.png"))
            bitmaps["dirt"] = BitmapFactory.decodeStream(am.open("pics/dirt.png"))
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    override fun surfaceCreated(holder: SurfaceHolder) {
        // Layout UI
        val w = width
        val h = height
        btnLeft.set(50, h - 250, 250, h - 50)
        btnRight.set(300, h - 250, 500, h - 50)
        btnAction.set(w - 500, h - 250, w - 300, h - 50)
        btnJump.set(w - 250, h - 250, w - 50, h - 50)

        isRunning = true
        thread = Thread(this)
        thread?.start()
    }

    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {}

    override fun surfaceDestroyed(holder: SurfaceHolder) {
        isRunning = false
        thread?.join()
    }

    override fun run() {
        while (isRunning) {
            if (holder.surface.isValid) {
                val canvas = holder.lockCanvas()
                drawGame(canvas)
                holder.unlockCanvasAndPost(canvas)
            }
        }
    }

    private fun drawGame(canvas: Canvas) {
        canvas.drawColor(Color.parseColor("#87CEEB")) // Sky color
        
        // Draw some ground
        val dirt = bitmaps["dirt"]
        if (dirt != null) {
            for (i in 0..width step dirt.width) {
                canvas.drawBitmap(dirt, i.toFloat(), height - dirt.height.toFloat(), paint)
            }
        }
        
        // Draw player (hardcoded for now to see something)
        val cat = bitmaps["cat"]
        if (cat != null) {
            canvas.drawBitmap(cat, width/2f, height/2f, paint)
        }
        
        // Draw UI
        paint.color = Color.argb(128, 200, 200, 200)
        canvas.drawRect(btnLeft, paint)
        canvas.drawRect(btnRight, paint)
        canvas.drawRect(btnJump, paint)
        canvas.drawRect(btnAction, paint)
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        val keys = JSONArray()
        
        for (i in 0 until event.pointerCount) {
            val x = event.getX(i).toInt()
            val y = event.getY(i).toInt()
            
            if (btnLeft.contains(x, y)) keys.put("left")
            if (btnRight.contains(x, y)) keys.put("right")
            if (btnJump.contains(x, y)) keys.put("jump")
            if (btnAction.contains(x, y)) keys.put("place") // generic action
        }
        
        val payload = JSONObject()
        payload.put("cmd", "input")
        payload.put("keys", keys)
        networkClient.send(payload)
        
        return true
    }
}
