import React, { createRef } from "react";
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, Button } from 'react-native';
import { SyncClient } from "twilio-sync";
import { getDeviceAccessToken } from "../Dialer/assets/library/api";
import Dialer from "../Dialer/Dialer";
import { SECONDARY_DEVICE_INFO_MESSAGE } from "../Dialer/assets/library/constant";


class CallButton extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            showCallListContainer: false,
            user: {
                number: "+14153297580",
                tenant_id: "painter-bros",
                subtenant_id: "da58532b-ac74-497d-8935-d0e891cfe21f"
            },
            isTwilioDeviceInitialized: true,
            shouldDisplayPopup: false,
            isTwilioDeviceInitializationMessage: "",
            deviceAccessToken: null,
            chatAccessToken: null,
            syncAccessToken: null,
            callLogAccessToken: null,
            deviceId: null,
            sync_list_call_obj_template: null,
            syncClient: null,
            syncDocument: null,
            isPrimaryDevice: false,
            shouldDisplayRedDot: {
                calls: { count: 0, activeCallDirection: [], isAnyCallOnProgress: [] },
                messages: false,
                callLogs: false
            }
        }
        this.syncErrorRetryCount = 0;
        this.target = createRef(null);
        this.child = createRef(null);
        this.setAllUnreadCounts = this.setAllUnreadCounts.bind(this);
    }
    componentDidMount() {
        const { user } = this.state;
        const getDeviceAccessTokenResponse = getDeviceAccessToken(
            user.number,
            user.tenant_id,
            user.subtenant_id
        );
        getDeviceAccessTokenResponse
            .then((accessTokenResponse) => {
                debugger;
                this.setState(
                    {
                        ...this.state,
                        deviceId: accessTokenResponse.data.device_id,
                        deviceAccessToken: accessTokenResponse.data.device_access_token,
                        chatAccessToken: accessTokenResponse.data.chat_access_token,
                        syncAccessToken: accessTokenResponse.data.sync_access_token,
                        sync_list_call_obj_template:
                            accessTokenResponse.data.sync_list_call_obj_template,
                        callLogAccessToken:
                            accessTokenResponse.data.call_log_sync_access_token
                    },
                    () => {
                        debugger;
                        user.identity = accessTokenResponse.data.user.identity;
                        this.createSyncClient();
                    }
                );
            })
            .catch((e) => {
                debugger;
                this.updateDeviceMessage(
                    "Unable to register your device due to authentication failure"
                );
            });
    }
    updateSyncClient = (syncAccessToken) => {
        const { syncClient } = this.state;
        syncClient.updateToken(syncAccessToken);
        this.setState({ ...this.state, syncAccessToken }, () =>
            this.createOrOpenSyncDocument()
        );
    };

    createOrOpenSyncDocument = () => {
        const { user } = this.state;
        const { syncClient } = this.state;
        if (!user) return;
        syncClient
            .document(user.identity)
            .then((document) => {
                console.log("Successfully opened a document. SID:", document.sid);

                document.on("removed", (args) => {
                    document.close();
                    if (syncClient) {
                        this.createOrOpenSyncDocument();
                    }
                });

                this.setState({ ...this.state, syncDocument: document }, async () => {
                    const { syncDocument, deviceId } = this.state;
                    syncDocument.on("updated", (event) => {
                        console.log('Received an "updated" event: ', event);
                        if (
                            event.data.primaryDeviceId === deviceId ||
                            event.data.primaryDeviceId === null
                        ) {
                            this.setState({
                                ...this.state,
                                isPrimaryDevice: true,
                                isTwilioDeviceInitializationMessage: "",
                                shouldDisplayPopup: false
                            });
                        } else {
                            this.updateDeviceMessage(SECONDARY_DEVICE_INFO_MESSAGE);
                        }
                    });
                    if (
                        syncDocument.revision === "0" ||
                        syncDocument.data.primaryDeviceId === null
                    ) {
                        this.setState({
                            ...this.state,
                            isPrimaryDevice: true,
                            isTwilioDeviceInitializationMessage: "",
                            shouldDisplayPopup: false
                        });
                    } else {
                        if (syncDocument.data.primaryDeviceId !== null) {
                            this.updateDeviceMessage(SECONDARY_DEVICE_INFO_MESSAGE);
                        }
                    }
                });
            })
            .catch((error) => {
                console.error("Unexpected error", error);
            });
    };
    updateDeviceMessage = (msg) => {
        console.log("msg",msg);
        this.setState({
            ...this.state,
            isTwilioDeviceInitializationMessage: msg,
            isPrimaryDevice: false,
            isTwilioDeviceInitialized: false
        });
    };
    createSyncClient = () => {
        const { syncAccessToken } = this.state;
        debugger;
        console.log("syncAccessToken:", syncAccessToken);
        const syncClient = new SyncClient(syncAccessToken);

        syncClient.on("connectionStateChanged", (newState) => {
            console.log("Received a new connection state:", newState);
            if (newState === "connected") {
                this.setState({ ...this.state, syncClient: syncClient }, () =>
                    this.createOrOpenSyncDocument()
                );
            }
        });

        syncClient.on("connectionError", (connectionError) => {
            console.log("Connection was interrupted:", connectionError);
            if (this.child.current) {
                this.child.current.destroyTwilioDevice();
            }
            const syncClientRetryingMsg =
                "A connection error occured, retrying in 10 seconds";
            this.updateDeviceMessage(syncClientRetryingMsg);
            if (syncClient) {
                syncClient.shutdown();
                if (this.syncErrorRetryCount < 18) {
                    this.syncErrorRetryCount += 1;
                    console.log(syncClientRetryingMsg);
                    setTimeout(() => {
                        this.createSyncClient();
                    }, 10000);
                } else {
                    this.updateDeviceMessage(
                        "Could not reestablish the connection after several attempts. Please try reloading the page."
                    );
                }
            }
        });
    };
    handleDialer = (keepOpen = false) => {
        const {
            showCallListContainer,
            isTwilioDeviceInitializationMessage,
            shouldDisplayPopup
        } = this.state;
        console.log(showCallListContainer,isTwilioDeviceInitializationMessage,shouldDisplayPopup);

        debugger;
        this.setState({
            ...this.state,
            showCallListContainer:
                !keepOpen && showCallListContainer === keepOpen
                    ? !showCallListContainer
                    : keepOpen,
            shouldDisplayPopup:
                isTwilioDeviceInitializationMessage === "" ? false : !shouldDisplayPopup
        });
        // this.makeChildOutGoingCall()
    };

    alterPopupDisplay = () => {
        const { shouldDisplayPopup } = this.state;
        debugger;
        this.setState({
            ...this.state,
            shouldDisplayPopup: !shouldDisplayPopup
        });
    };
    checkTwilioDeviceInitializeStatus = (currentStatus) => {
        console.log("checkTwilioDeviceInitializeStatus:",currentStatus)
        debugger;
        this.setState({
            ...this.state,
            isTwilioDeviceInitialized: currentStatus,
            isTwilioDeviceInitializationMessage: "",
            shouldDisplayPopup: false
        });
    };

    popover = () => {
        const { isTwilioDeviceInitializationMessage } = this.state;
        return (
            <Popover id="popover-basic">
                <Popover.Body>{isTwilioDeviceInitializationMessage}</Popover.Body>
            </Popover>
        );
    };

    setAllUnreadCounts = (itemType, status, countableObject) => {
        const countedObject = {
            calls: { count: 0, activeCallDirection: [], isAnyCallOnProgress: [] },
            messages: false,
            callLogs: false
        };
        if (itemType === "calls") {
            countedObject.calls.count = Object.values(countableObject).length;
            countedObject.calls.activeCallDirection = Object.values(
                countableObject
            ).filter((element) => element.conference.status === "in-progress");
            countedObject.calls.isAnyCallOnProgress = Object.values(
                countableObject
            ).filter(
                (element) =>
                    !["initiated", "ringing"].includes(element.conference.status)
            );
        }
        if (itemType === "messages") {
            countedObject.messages = status;
        }
        if (itemType === "callLogs") {
            countedObject.callLogs = status;
        }
        this.setState({ ...this.state, shouldDisplayRedDot: { ...countedObject } });
    };

    getNotificationIcon = () => {
        const { shouldDisplayRedDot } = this.state;
        if (shouldDisplayRedDot.calls.isAnyCallOnProgress.length > 0) {
            if (shouldDisplayRedDot.calls.activeCallDirection.length === 0) {
                return `${REACT_APP_STATIC_ASSETS_BASE_URL}${smallpauseicon}`;
            }
            if (
                shouldDisplayRedDot.calls.activeCallDirection[0].call.direction ===
                "outbound-api"
            ) {
                return `${REACT_APP_STATIC_ASSETS_BASE_URL}${outgoingcallicon}`;
            }

            if (
                shouldDisplayRedDot.calls.activeCallDirection[0].call.direction ===
                "inbound"
            ) {
                return `${REACT_APP_STATIC_ASSETS_BASE_URL}${inboundicon}`;
            }
        } else {
            return `${REACT_APP_STATIC_ASSETS_BASE_URL}${whitecallicon}`;
        }
    };
    render() {
        const {
            showCallListContainer,
            isTwilioDeviceInitialized,
            isTwilioDeviceInitializationMessage,
            shouldDisplayPopup,
            deviceAccessToken,
            chatAccessToken,
            syncAccessToken,
            callLogAccessToken,
            deviceId,
            sync_list_call_obj_template,
            syncClient,
            isPrimaryDevice,
            syncDocument,
            shouldDisplayRedDot
        } = this.state;
        console.log("isTwilioDeviceInitialized:",isTwilioDeviceInitialized);
        console.log("showCallListContainer:",showCallListContainer);
        const { user } = this.state;
        return (
            <View>
                <Button
                    title="Call"
                    color="#841584"
                    onPress={() =>
                        isTwilioDeviceInitialized
                            ? this.handleDialer()
                            : this.alterPopupDisplay()
                    }
                >
                </Button>
                {isPrimaryDevice && (
                    <Dialer
                        ref={this.child}
                        user={user}
                        checkTwilioDeviceInitializeStatus={
                            this.checkTwilioDeviceInitializeStatus
                        }
                        showCallListContainer={showCallListContainer}
                        handleDialer={this.handleDialer}
                        deviceAccessToken={deviceAccessToken}
                        chatAccessToken={chatAccessToken}
                        syncAccessToken={syncAccessToken}
                        callLogAccessToken={callLogAccessToken}
                        deviceId={deviceId}
                        sync_list_call_obj_template={sync_list_call_obj_template}
                        syncClient={syncClient}
                        syncDocument={syncDocument}
                        updateDeviceMessage={this.updateDeviceMessage}
                        shouldDisplayRedDot={shouldDisplayRedDot}
                        updateSyncClient={this.updateSyncClient}
                        setAllUnreadCounts={this.setAllUnreadCounts}
                    />
                )}
            </View>
        )
    }
}

export default CallButton;