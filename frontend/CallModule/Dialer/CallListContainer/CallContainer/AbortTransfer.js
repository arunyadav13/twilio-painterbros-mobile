import React from "react";
import { Button, Image,Text } from "react-native";
import warmtransferabort from "../../../Dialer/CallListContainer/assets/images/warmtransferabort.svg";

const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class AbortTransfer extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const { abortTransfer, callElement } = this.props;
    return (
      <Button
        disabled={window.shouldDisableTransferActionBtn}
        className="removecolorbut"
        onPress={() => {
          window.shouldDisableTransferActionBtn = true;
          abortTransfer(callElement);
        }}
      >
        <Image
          source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${warmtransferabort}`}
        />
        <Text>Abort Transfer</Text>
      </Button>
    );
  }
}

export default AbortTransfer;
