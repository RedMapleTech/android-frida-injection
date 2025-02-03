import frida
import sys

# The Frida script above is stored in a variable
FRIDA_SCRIPT = """
Java.perform(function () {
    console.log("[*] WebSocket Hook Started...");

    Java.enumerateLoadedClasses({
        onMatch: function (classname) {
            if (classname.toLowerCase().includes("websocket")) {
                console.log("[*] Found WebSocket class: " + classname);

                try {
                    var WebSocket = Java.use(classname);
                    WebSocket.send.overloads.forEach(function (overload) {
                        overload.implementation = function () {
                            var message = arguments[0];
                            console.log("[SEND] " + message);
                            send({ "type": "send", "class": classname, "message": message });

                            return overload.apply(this, arguments);
                        };
                    });

                    console.log("[*] Hooked: " + classname + ".send()");

                } catch (err) {
                    console.log("[!] Failed to hook: " + classname + " - " + err);
                }
            }
        },
        onComplete: function () {
            console.log("[*] WebSocket class enumeration complete.");
        }
    });

    try {
        Java.enumerateLoadedClasses({
            onMatch: function (classname) {
                if (classname.toLowerCase().includes("websocketlistener")) {
                    console.log("[*] Found WebSocketListener class: " + classname);

                    try {
                        var WebSocketListener = Java.use(classname);
                        WebSocketListener.onMessage.overloads.forEach(function (overload) {
                            overload.implementation = function (ws, message) {
                                console.log("[RECEIVE] " + message);
                                send({ "type": "receive", "class": classname, "message": message });

                                return overload.apply(this, arguments);
                            };
                        });

                        console.log("[*] Hooked: " + classname + ".onMessage()");

                    } catch (err) {
                        console.log("[!] Failed to hook: " + classname + " - " + err);
                    }
                }
            },
            onComplete: function () {
                console.log("[*] WebSocketListener class enumeration complete.");
            }
        });
    } catch (err) {
        console.log("[!] Failed to enumerate WebSocketListeners: " + err);
    }
});
"""

# Function to handle messages from Frida
def on_message(message, data):
    try:
        if "payload" in message:
            ws_type = message["payload"]["type"].upper()
            ws_message = message["payload"]["message"]
            print(f"[{ws_type}] {ws_message}")

    except Exception as e:
        print(f"[ERROR] Logging error: {e}")

# Attach Frida script to a running process
def attach_to_process(device, pid):
    try:
        session = device.attach(int(pid))
        script = session.create_script(FRIDA_SCRIPT)
        script.on("message", on_message)
        script.load()

        print(f"[*] Hooking WebSocket messages in process {pid}. Press Ctrl+C to stop.")
        sys.stdin.read()

    except Exception as e:
        print(f"[ERROR] {e}")

# Launch an app and attach to it
def spawn_and_attach(device, package_name):
    try:
        pid = device.spawn([package_name])
        print(f"[*] Spawned {package_name} with PID {pid}")

        device.resume(pid)
        attach_to_process(device, pid)

    except Exception as e:
        print(f"[ERROR] {e}")

# Main function to decide whether to attach or spawn
def main():
    if len(sys.argv) < 3:
        print("Usage: python hook_websockets.py --pid <pid>")
        print("   or  python hook_websockets.py --spawn <package_name>")
        sys.exit(1)

    device = frida.get_usb_device()

    mode = sys.argv[1]
    target = sys.argv[2]

    if mode == "--pid":
        attach_to_process(device, target)
    elif mode == "--spawn":
        spawn_and_attach(device, target)
    else:
        print("Invalid option. Use '--pid <pid>' to attach or '--spawn <package_name>' to launch an app.")
        sys.exit(1)

if __name__ == "__main__":
    main()
