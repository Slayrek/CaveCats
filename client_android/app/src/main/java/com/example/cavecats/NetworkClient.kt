package com.example.cavecats

import android.util.Log
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter
import java.net.Socket
import kotlin.concurrent.thread

class NetworkClient {
    private var socket: Socket? = null
    private var out: PrintWriter? = null
    private var inReader: BufferedReader? = null
    var isConnected = false
    
    // Callbacks to handle messages from server
    var onChunkDataReceived: ((JSONObject) -> Unit)? = null
    var onEntitySyncReceived: ((JSONObject) -> Unit)? = null
    
    fun connect(host: String, port: Int) {
        thread {
            try {
                socket = Socket(host, port)
                out = PrintWriter(socket!!.outputStream, true)
                inReader = BufferedReader(InputStreamReader(socket!!.inputStream))
                isConnected = true
                Log.d("NetworkClient", "Connected to server")
                
                // Initial packet to set name
                val initPacket = JSONObject()
                initPacket.put("cmd", "sync")
                initPacket.put("name", "AndroidPlayer")
                initPacket.put("x", 0)
                initPacket.put("y", 0)
                send(initPacket)
                
                listen()
            } catch (e: Exception) {
                Log.e("NetworkClient", "Error connecting: ${e.message}")
                isConnected = false
            }
        }
    }
    
    private fun listen() {
        try {
            while (isConnected) {
                val line = inReader?.readLine() ?: break
                if (line.isNotEmpty()) {
                    try {
                        val obj = JSONObject(line)
                        when (obj.optString("cmd")) {
                            "world_sync" -> onChunkDataReceived?.invoke(obj)
                            "entity_sync" -> onEntitySyncReceived?.invoke(obj)
                        }
                    } catch (e: Exception) {
                        Log.e("NetworkClient", "JSON Parse error: ${e.message}")
                    }
                }
            }
        } catch (e: Exception) {
            Log.e("NetworkClient", "Error reading: ${e.message}")
        } finally {
            disconnect()
        }
    }
    
    fun send(json: JSONObject) {
        if (!isConnected) return
        thread {
            try {
                out?.println(json.toString())
            } catch (e: Exception) {
                Log.e("NetworkClient", "Send error: ${e.message}")
            }
        }
    }
    
    fun disconnect() {
        isConnected = false
        try { out?.close() } catch (e: Exception) {}
        try { inReader?.close() } catch (e: Exception) {}
        try { socket?.close() } catch (e: Exception) {}
    }
}
