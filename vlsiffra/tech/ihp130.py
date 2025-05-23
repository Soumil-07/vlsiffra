from amaranth import Elaboratable, Module, Signal, Instance

class _IHP130_FA_Core(Elaboratable):
    """
    Ports: a, b, ci (inputs); co, x (outputs)
    x is sum, co is carry_out.
    """

    def __init__(self, a, b, ci, co, x):
        self.a = a
        self.b = b
        self.ci = ci
        self.co = co
        self.x = x

    def elaborate(self, platform):
        m = Module()
        _0_ = Signal(name=f"fa_internal_0_U{id(self):x}")
        _1_ = Signal(name=f"fa_internal_1_U{id(self):x}")

        m.submodules.fa_inst_2 = Instance(
            "sg13g2_and2_1", i_A=self.a, i_B=self.ci, o_X=_0_
        )
        m.submodules.fa_inst_3 = Instance(
            "sg13g2_xor2_1", i_A=self.a, i_B=self.ci, o_X=_1_
        )
        m.submodules.fa_inst_4 = Instance(
            "sg13g2_a21o_1", i_A1=self.b, i_A2=_1_, i_B1=_0_, o_X=self.co
        )
        m.submodules.fa_inst_5 = Instance(
            "sg13g2_xor2_1", i_A=self.b, i_B=_1_, o_X=self.x
        )
        return m


class _IHP130_HA_Core(Elaboratable):
    """
    Implements a Half Adder based on the netlist provided in ha.out.v.txt.
    Ports: a, b (inputs); co, x (outputs)
    x is sum, co is carry_out.
    """

    def __init__(self, a, b, co, x):
        self.a = a
        self.b = b
        self.co = co
        self.x = x

    def elaborate(self, platform):
        m = Module()
        m.submodules.ha_inst_0 = Instance(
            "sg13g2_and2_1", i_A=self.a, i_B=self.b, o_X=self.co
        )
        m.submodules.ha_inst_1 = Instance(
            "sg13g2_xor2_1", i_A=self.a, i_B=self.b, o_X=self.x
        )
        return m


class _IHP130_AO33_Core(Elaboratable):
    """
    Implements an AO33 ( (A1&A2&A3) | (B1&B2&B3) ) gate
    based on the netlist provided in ao33.out.v.txt.
    The netlist implements o = (a1&a2&a3) | (b1&b2&b3).
    """

    def __init__(self, a1, a2, a3, b1, b2, b3, o):
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.o = o

    def elaborate(self, platform):
        m = Module()
        _0_ = Signal(name=f"ao33_internal_0_U{id(self):x}")
        _1_ = Signal(name=f"ao33_internal_1_U{id(self):x}")

        m.submodules.ao33_inst_2 = Instance(
            "sg13g2_nand3_1",
            i_A=self.b2,
            i_B=self.b1,
            i_C=self.b3,
            o_Y=_0_,
        )
        m.submodules.ao33_inst_3 = Instance(
            "sg13g2_nand3_1",
            i_A=self.a2,
            i_B=self.a1,
            i_C=self.a3,
            o_Y=_1_,
        )
        m.submodules.ao33_inst_4 = Instance(
            "sg13g2_nand2_1", i_A=_0_, i_B=_1_, o_Y=self.o
        )
        return m


class IHP130Process(Elaboratable):
    def __init__(self, powered=False):
        self._powered = powered

    def _PoweredInstance(self, cell_type, **kwargs):
        return Instance(cell_type, **kwargs)

    def _generate_and(self, a, b, o):
        andgate = self._PoweredInstance(
            "sg13g2_and2_1", i_A=a, i_B=b, o_X=o
        )
        self.m.submodules += andgate

    def _generate_xor(self, a, b, o):
        xorgate = self._PoweredInstance(
            "sg13g2_xor2_1", i_A=a, i_B=b, o_X=o  # Maps to Verilog port X
        )
        self.m.submodules += xorgate

    def _generate_inv(self, a, o):
        invgate = self._PoweredInstance(
            "sg13g2_inv_1", i_A=a, o_Y=o  # Maps to Verilog port Y
        )
        self.m.submodules += invgate

    def _generate_full_adder(self, a, b, carry_in, sum_out, carry_out, name=None):
        fa_core_instance = _IHP130_FA_Core(
            a=a, b=b, ci=carry_in, co=carry_out, x=sum_out
        )

        if name:
            self.m.submodules[name] = fa_core_instance
        else:
            self.m.submodules += fa_core_instance

    def _generate_half_adder(self, a, b, sum_out, carry_out, name=None):
        ha_core_instance = _IHP130_HA_Core(a=a, b=b, co=carry_out, x=sum_out)

        if name:
            self.m.submodules[name] = ha_core_instance
        else:
            self.m.submodules += ha_core_instance

    def _generate_ao21(self, a1, a2, b1, o):
        """2-input AND into first input of 2-input OR. o = (a1 & a2) | b1"""
        a21o_gate = self._PoweredInstance(
            "sg13g2_a21o_1",
            i_A1=a1,
            i_A2=a2,
            i_B1=b1,
            o_X=o,
        )
        self.m.submodules += a21o_gate

    def _generate_ao22(self, a1, a2, b1, b2, o):
        """2-input AND into both inputs of 2-input OR. o = (a1 & a2) | (b1 & b2)"""

        a22oi_out_signal = Signal(name=f"ao22_internal_a22oi_out_U{id(self):x}")

        a22oi_gate = self._PoweredInstance(
            "sg13g2_a22oi_1",
            i_A1=a1,
            i_A2=a2,
            i_B1=b1,
            i_B2=b2,
            o_Y=a22oi_out_signal,
        )
        self.m.submodules += (
            a22oi_gate
        )

        inv_for_ao22 = self._PoweredInstance(
            "sg13g2_inv_1", i_A=a22oi_out_signal, o_Y=o 
        )
        self.m.submodules += (
            inv_for_ao22
        )

    def _generate_ao33(self, a1, a2, a3, b1, b2, b3, o):
        """3-input AND into both inputs of 2-input OR. o = (a1&a2&a3) | (b1&b2&b3)"""
        ao33_core_instance = _IHP130_AO33_Core(
            a1=a1, a2=a2, a3=a3, b1=b1, b2=b2, b3=b3, o=o
        )

        self.m.submodules += ao33_core_instance
