package com.example.cavecats

import android.os.Bundle
import android.view.WindowInsets
import android.view.WindowInsetsController
import androidx.activity.ComponentActivity

class MainActivity : ComponentActivity() {
    private lateinit var gameView: GameView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Hide UI for fullscreen immersive mode
        window.insetsController?.let {
            it.hide(WindowInsets.Type.statusBars() or WindowInsets.Type.navigationBars())
            it.systemBarsBehavior = WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }

        gameView = GameView(this)
        setContentView(gameView)
        
        // TODO: Replace with the actual IP address of the Python relay server
        gameView.networkClient.connect("10.0.2.2", 7777)
    }

    override fun onDestroy() {
        super.onDestroy()
        gameView.networkClient.disconnect()
    }
}
